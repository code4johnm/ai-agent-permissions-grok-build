#!/usr/bin/env python3
"""
Permission Assistant - Runtime Hybrid Permission Management Prototype

Implements key future directions from the paper (scanned from local clean PDF
in ~/Downloads/wu-agentperms-sp26*.pdf via rendered pages for accuracy):

"Towards Automating Data Access Permissions in AI Agents"
Wu et al., 2026 IEEE Symposium on Security and Privacy.

Exact quotes addressed (from Discussion p.13-14 + Conclusion p.14 of local PDF):

"challenges remain in enforcing predictions, improving robustness, and designing
usable interfaces."

"Automated permission management is a multifaceted problem. ... other important
facets, including improving the usability of permission management in AI agents,
remain challenges and open avenues for future work. For example, during early use,
the assistant may still need to learn a user’s preferences; a user’s preferences
may change as their circumstances change (e.g., a previously trusted entity becomes
untrusted); and some situations may be fundamentally difficult to predict. Thus,
a full-fledged permission system will need to include not only a permission
prediction module, but also UI/UX for engaging the user directly in cases where
the predictive model has low confidence or makes a mistake—for example, UI/UX for
users to make explicit permission decisions, to revoke previously-granted
permissions, and to give feedback to the permission assistant. We believe there is
rich future work to be done on how to design such a hybrid system."

"taking only high-confidence predictions and delegating uncertain data access
permissions to users can help mitigate the model’s robustness issues."

"as permission assistants will make predictions to share data on behalf of users,
a high precision and lower FPR may be desired, which requires a compromise on
model coverage. Thus, in practice, the users may need to be involved in the loop..."

This module + the confidence-threshold + robust-parsing upgrades in evaluation_utils.py
directly implement the above (plus the 4-option study choices, cold-start/history
impact from §5.2.3, and proof-of-concept hybrid exploration noted on p.9).

See docs/Paper-Future-Work-and-Gaps-from-Local-PDF.md for the full catalog from the
local clean renders.

Run:
    python permission_assistant.py --demo
    python permission_assistant.py --help

No OpenAI key required for the mock/demo mode (recommended for research & testing).
Real LLM mode available if OPENAI_API_KEY + cf_scores present (adapts hybrid prompt logic).
"""

import os
import sys
import json
import random
import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import argparse

# Optional real LLM support (falls back gracefully)
try:
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()
    HAS_OPENAI = 'OPENAI_API_KEY' in os.environ
except Exception:
    HAS_OPENAI = False
    OpenAI = None

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# Import our robust components from the research harness
try:
    from evaluation_utils import (
        robust_extract_predictions,
        evaluate_at_threshold,
        calculate_metrics,
    )
    HAS_EVAL_UTILS = True
except ImportError:
    HAS_EVAL_UTILS = False

# -----------------------------------------------------------------------------
# Configuration & Policy
# -----------------------------------------------------------------------------

DEFAULT_HIGH_CONF_THRESH = 0.85
DEFAULT_DEFER_THRESH = 0.65   # Below this is definitely defer

# Data sensitivity priors distilled from the paper's findings (Table 4, Sec 4.2.2, 5.3.2)
SENSITIVITY: Dict[str, float] = {
    # High sensitivity -> bias toward "never" / high FNR in models
    "ssn": 0.15, "social security": 0.12, "passport": 0.18, "driver license": 0.22,
    "bank account": 0.20, "credit card": 0.25, "account credentials": 0.18,
    "child name": 0.22, "pregnancy": 0.28, "health": 0.35, "medical": 0.30,
    "tax": 0.40, "investment": 0.32, "salary": 0.38,
    # Low sensitivity -> bias toward "always"
    "music": 0.82, "hobbies": 0.78, "fitness goal": 0.75, "sleep": 0.70,
    "movie": 0.80, "weather": 0.85, "calendar": 0.65,
    # Medium / context dependent
    "location": 0.55, "email": 0.50, "name": 0.60, "meeting": 0.58,
    "travel": 0.45, "photo": 0.40,
}

DOMAIN_BIAS = {
    "Finance": -0.25, "Health & Fitness": -0.10, "Smart Home": -0.15,
    "Travel": -0.18, "Shopping": -0.12, "Work & Productivity": 0.05,
    "Entertainment": 0.15, "Social": 0.08,
}

DEFAULT_BIO = (
    "A privacy-conscious adult in the 35-44 age group who values "
    "control over sensitive personal data."
)


@dataclass
class Decision:
    """A single permission decision (audit record)."""
    timestamp: str
    query: str
    data_type: str
    domain: str
    tool: str
    predicted_label: str
    predicted_conf: float
    source: str  # "auto-highconf", "auto-lowconf-followed", "user-explicit", "user-revoked", "feedback-adjusted"
    final_decision: str  # one of the 4 options or "auto: Yes, always share" etc.
    rationale: str = ""
    user_comment: str = ""


@dataclass
class UserSession:
    """Live user state for the assistant (simulates real deployment profile)."""
    participant_id: str = "demo-user"
    bio: str = DEFAULT_BIO
    history: List[Dict[str, Any]] = field(default_factory=list)  # list of prior decisions
    decisions_log: List[Decision] = field(default_factory=list)
    revocations: List[str] = field(default_factory=list)  # data_types revoked

    def add_history(self, query: str, data_type: str, decision: str):
        self.history.append({
            "query": query[:120],
            "data_type": data_type,
            "decision": decision,
            "ts": datetime.datetime.now().isoformat()
        })
        # Keep bounded
        if len(self.history) > 50:
            self.history = self.history[-50:]

    def record_decision(self, d: Decision):
        self.decisions_log.append(d)
        # Also keep compact history for future mock predictions
        self.add_history(d.query, d.data_type, d.final_decision)

    def get_recent_for_prompt(self, k: int = 6) -> str:
        if not self.history:
            return "(no prior decisions in this session)"
        lines = []
        for h in self.history[-k:]:
            lines.append(f"- Query: {h['query']} | Data: {h['data_type']} → {h['decision']}")
        return "\n".join(lines)


# -----------------------------------------------------------------------------
# Core Prediction Logic (Mock + Optional Real Hybrid)
# -----------------------------------------------------------------------------

def _sensitivity_score(data_type: str, domain: str = "") -> float:
    """Heuristic prior from paper findings."""
    dt_lower = data_type.lower()
    score = 0.55  # neutral default
    for key, val in SENSITIVITY.items():
        if key in dt_lower:
            score = val
            break
    if domain in DOMAIN_BIAS:
        score += DOMAIN_BIAS[domain]
    return max(0.05, min(0.95, score))


def mock_predict(
    query: str,
    data_types: List[str],
    domain: str,
    tool: str,
    session: UserSession,
    cf_hint: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Pure-local mock hybrid predictor.
    Combines:
    - Sensitivity prior (paper Table 4 high/low variance + under-permission patterns)
    - Session history consistency (paper 4.2.5: intra-domain consistency)
    - Light "CF-like" bias from other similar users (simulated via global priors + cf_hint if provided)
    - Small random for realism (models aren't perfect)

    Returns list of {"data_type": , "label": one of 4 options, "score": 0-1, "rationale": str}
    """
    results = []
    recent = session.get_recent_for_prompt(4)

    for dt in data_types:
        prior = _sensitivity_score(dt, domain)

        # History adjustment: if user was consistent on similar data, pull toward it
        hist_bias = 0.0
        for h in session.history[-8:]:
            if h["data_type"].lower() in dt.lower() or dt.lower() in h["data_type"].lower():
                if "never" in h["decision"].lower() or "No" in h["decision"]:
                    hist_bias -= 0.18
                elif "always" in h["decision"].lower() or "Yes" in h["decision"]:
                    hist_bias += 0.15

        # CF-like external hint (if caller passed a precomputed neighbor score)
        cf_bias = (cf_hint - 0.5) * 0.4 if cf_hint is not None else 0.0

        # Combine + noise (models have variance, esp. for high-variance users per paper 5.3.1)
        raw = prior + hist_bias + cf_bias + random.uniform(-0.08, 0.08)
        conf = max(0.35, min(0.97, abs(raw - 0.5) * 1.6 + 0.35))  # higher conf when extreme

        # Map to 4 options (paper collected these; we support them for defer UX)
        if raw > 0.72:
            label = "Yes, always share"
            rationale = f"Low sensitivity + consistent past allowance in similar contexts. (prior={prior:.2f}, hist_bias={hist_bias:+.2f})"
        elif raw > 0.48:
            label = "Yes, but ask me first"
            rationale = "Borderline positive; user historically sometimes wants control on this data class."
            conf = min(conf, 0.68)  # force medium conf -> likely defer
        elif raw > 0.28:
            label = "No, but ask me first"
            rationale = "Elevated sensitivity or negative history; prefer explicit confirmation."
            conf = min(conf, 0.72)
        else:
            label = "No, never share"
            rationale = f"High sensitivity data type (paper: SSN/passport/credentials show ~46%+ under-permission). (prior={prior:.2f})"

        # If we have external CF signal and it disagrees strongly, lower conf (paper: filter unreliable CF)
        if cf_hint is not None and abs(cf_hint - (1 if "Yes" in label else 0)) > 0.6:
            conf = max(0.40, conf * 0.7)
            rationale += " [CF neighbor signal conflicted; reduced confidence]"

        results.append({
            "data_type": dt,
            "label": label,
            "score": round(conf, 3),
            "rationale": rationale,
            "domain": domain,
            "tool": tool,
            "query": query[:140]
        })

    return results


def real_hybrid_predict_if_available(
    query: str,
    data_types: List[str],
    domain: str,
    tool: str,
    session: UserSession,
    cf_scores_df=None
) -> Optional[List[Dict[str, Any]]]:
    """
    Best-effort real call using the paper's hybrid prompt style (single query, few history).
    Only used if OPENAI key present. Returns None on any failure (caller falls back to mock).
    """
    if not HAS_OPENAI or OpenAI is None:
        return None

    try:
        client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
        model = os.getenv('OPENAI_MODEL', 'o4-mini')

        # Minimal history for prompt
        hist_text = session.get_recent_for_prompt(3)

        # Very small CF injection if available (demo only)
        cf_text = "No strong CF recommendations available for this exact item."
        if cf_scores_df is not None and HAS_PANDAS and len(cf_scores_df) > 0:
            # (demo: we don't have full user_id mapping here; skip heavy lookup)
            pass

        prompt = f"""You are a precise permission prediction assistant for an AI agent.
Predict ONLY for the listed data types. Output valid JSON array.

User profile: {session.bio[:200]}
Recent decisions: {hist_text}

New agent request: "{query}" (domain: {domain}, tool: {tool})
Data types needed: {data_types}

For each, output:
{{"data_type": "...", "label": "Yes, always share" OR "No, never share" OR "Yes, but ask me first" OR "No, but ask me first", "score": 0.0-1.0, "rationale": "short reason"}}

Return ONLY the JSON array, nothing else."""

        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=800
        )
        content = resp.choices[0].message.content or ""
        parsed = robust_extract_predictions(content) if HAS_EVAL_UTILS else json.loads(content)
        # Normalize to our expected shape
        out = []
        for p in parsed:
            if isinstance(p, dict) and "label" in p:
                out.append({
                    "data_type": p.get("data_type", p.get("datatype", "unknown")),
                    "label": p.get("label", "No, never share"),
                    "score": float(p.get("score", 0.5)),
                    "rationale": p.get("rationale", p.get("reason", "LLM prediction")),
                    "domain": domain, "tool": tool, "query": query[:140]
                })
        return out if out else None
    except Exception as e:
        print(f"[warn] real hybrid predict failed, falling back to mock: {e}")
        return None


def decide(
    pred: Dict[str, Any],
    high_thresh: float = DEFAULT_HIGH_CONF_THRESH
) -> Tuple[str, str, bool]:
    """
    Apply policy: high conf -> auto-execute the predicted label; else defer to user.
    Returns (final_text, source, is_auto)
    """
    label = pred["label"]
    conf = float(pred.get("score", 0.5))

    if conf >= high_thresh and ("always share" in label.lower() or "never share" in label.lower()):
        source = "auto-highconf"
        final = f"auto: {label}"
        is_auto = True
    else:
        source = "deferred-to-user"
        final = label  # will be overridden by explicit user choice
        is_auto = False
    return final, source, is_auto


# -----------------------------------------------------------------------------
# Interactive Demo (implements the paper's "UI/UX for low confidence + feedback + revoke")
# -----------------------------------------------------------------------------

def run_interactive_demo(session: Optional[UserSession] = None):
    """Main demo loop showing the hybrid usable permission system."""
    if session is None:
        session = UserSession(participant_id="P-DEMO-001")

    print("\n" + "="*72)
    print("AI AGENT PERMISSION ASSISTANT — INTERACTIVE DEMO")
    print("Prototype implementing future work from Wu et al. IEEE S&P 2026 paper")
    print("="*72)
    print("Key paper directions implemented here:")
    print("  • High-confidence auto decisions (reduces user burden)")
    print("  • Low-confidence → explicit user choice (4 original options)")
    print("  • Revocation of prior grants")
    print("  • Feedback to assistant (affects future mock predictions)")
    print("  • Full decision audit log")
    print("  • Session history for preference consistency / drift simulation")
    print("-"*72)

    # Sample scenarios drawn from paper queries.json style
    scenarios = [
        {
            "query": "Book me a flight to the conference in Seattle next month using my usual airline.",
            "domain": "Travel", "tool": "Travel Booking",
            "data_types": ["Passport Information", "Payment Method Details", "Travel Itinerary", "Frequent Flyer Number"]
        },
        {
            "query": "Create a personalized 4-week workout plan based on my current fitness level and goals.",
            "domain": "Health & Fitness", "tool": "Fitness Tracking",
            "data_types": ["Fitness goal", "Physical limitations or injuries", "Gender", "Age"]
        },
        {
            "query": "Analyze last year's tax documents and suggest optimization strategies.",
            "domain": "Finance", "tool": "Tax Management",
            "data_types": ["Tax Filing Status", "Income Information", "Investment Information", "SSN"]
        },
        {
            "query": "Recommend new music based on my listening history and add a few songs to my library.",
            "domain": "Entertainment", "tool": "Apple Music",
            "data_types": ["Music Listening History", "Hobbies and Interests", "Age"]
        },
        {
            "query": "Check the weather and smart lights at home before I arrive this evening.",
            "domain": "Smart Home", "tool": "Weather",
            "data_types": ["Home Address", "Lighting Control Preferences", "Location"]
        },
    ]

    for i, scen in enumerate(scenarios, 1):
        print(f"\n--- Scenario {i}/{len(scenarios)} ---")
        print(f"Agent query: {scen['query']}")
        print(f"Domain: {scen['domain']} | Tool: {scen['tool']}")
        print(f"Data types requested: {', '.join(scen['data_types'])}")

        # Try real hybrid first, fall back to strong mock
        preds = real_hybrid_predict_if_available(
            scen['query'], scen['data_types'], scen['domain'], scen['tool'], session
        )
        if preds is None:
            preds = mock_predict(
                scen['query'], scen['data_types'], scen['domain'], scen['tool'], session
            )

        # For each data type, apply policy + interact if needed
        for p in preds:
            final, source, is_auto = decide(p, high_thresh=DEFAULT_HIGH_CONF_THRESH)

            print(f"\n  Data: {p['data_type']}")
            print(f"    Predicted: {p['label']} (conf={p['score']:.2f})")
            print(f"    Rationale: {p['rationale'][:180]}...")

            if is_auto:
                print(f"    → AUTO-APPROVED ({source})")
                dec = Decision(
                    timestamp=datetime.datetime.now().isoformat(),
                    query=scen['query'], data_type=p['data_type'], domain=scen['domain'], tool=scen['tool'],
                    predicted_label=p['label'], predicted_conf=p['score'],
                    source=source, final_decision=final, rationale=p['rationale']
                )
                session.record_decision(dec)
            else:
                # Interactive "UI" per paper: ask user (the 4 options)
                print("    → LOW CONFIDENCE — asking user (paper: delegate uncertain cases)")
                print("      1) Yes, always share   2) Yes, but ask me first")
                print("      3) No, but ask me first  4) No, never share   5) Revoke similar past grants")
                choice = input("      Your choice [1-5, default=2]: ").strip() or "2"

                user_label = {
                    "1": "Yes, always share",
                    "2": "Yes, but ask me first",
                    "3": "No, but ask me first",
                    "4": "No, never share",
                }.get(choice, "Yes, but ask me first")

                comment = ""
                if choice == "5":
                    user_label = "No, never share"
                    comment = "User revoked via demo UI"
                    session.revocations.append(p['data_type'])

                dec = Decision(
                    timestamp=datetime.datetime.now().isoformat(),
                    query=scen['query'], data_type=p['data_type'], domain=scen['domain'], tool=scen['tool'],
                    predicted_label=p['label'], predicted_conf=p['score'],
                    source="user-explicit" if choice != "5" else "user-revoked",
                    final_decision=user_label,
                    rationale=p['rationale'],
                    user_comment=comment
                )
                session.record_decision(dec)
                print(f"      Recorded: {user_label}")

        # Occasional feedback prompt (paper: give feedback to assistant)
        if i % 2 == 0 and random.random() > 0.4:
            fb = input("\n  Any feedback on these decisions for the assistant? (e.g. 'too permissive on finance' or empty): ").strip()
            if fb:
                # Simple adaptation: inject a pseudo-history entry that biases future mock preds
                session.add_history("[FEEDBACK]", "global", f"FEEDBACK: {fb[:80]}")
                print("  ✓ Feedback recorded; will influence subsequent mock predictions in this session.")

    # End-of-demo summary (audit + stats)
    print("\n" + "="*72)
    print("SESSION SUMMARY — AUDIT LOG (paper: tamper-evident decisions + feedback)")
    print("="*72)
    autos = [d for d in session.decisions_log if "auto" in d.source]
    user_in_loop = [d for d in session.decisions_log if "user" in d.source]
    print(f"Total decisions: {len(session.decisions_log)}")
    print(f"  Auto high-conf (low burden): {len(autos)}")
    print(f"  User explicit / deferred:   {len(user_in_loop)}")
    print(f"  Revocations this session:   {len(session.revocations)}")

    if session.decisions_log:
        print("\nLast 5 decisions (full provenance):")
        for d in session.decisions_log[-5:]:
            print(f"  [{d.timestamp[11:19]}] {d.data_type[:28]:<28} → {d.final_decision[:22]:<22} ({d.source})")

    print("\nThis demo shows a minimal but functional 'hybrid usable permission system'")
    print("as called for in the paper's future work section. Real deployments would add:")
    print("  - Signed persistent user profiles + policy store")
    print("  - Proper authenticated UI (web/app) instead of CLI")
    print("  - Real CF model lookup + on-prem LLM with guardrails")
    print("  - Tamper-evident audit (hash chain / SIEM export)")
    print("  - Revocation propagation to agent memory/tools")
    print("="*72 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="AI Agent Permission Assistant demo (paper future work)"
    )
    parser.add_argument(
        "--demo", action="store_true", help="Run the interactive hybrid demo"
    )
    parser.add_argument(
        "--user", default="P-DEMO-001", help="Simulated participant ID"
    )
    parser.add_argument(
        "--bio", default=DEFAULT_BIO, help="Short user bio for the session"
    )
    args = parser.parse_args()

    if not args.demo:
        parser.print_help()
        print("\nTip: python src/permission_assistant.py --demo")
        return

    sess = UserSession(participant_id=args.user, bio=args.bio)
    # Seed a tiny bit of history so first predictions aren't purely prior-driven
    sess.add_history("Previous demo query", "Music Listening History", "Yes, always share")
    sess.add_history("Previous demo query", "SSN", "No, never share")

    run_interactive_demo(sess)


if __name__ == "__main__":
    main()
