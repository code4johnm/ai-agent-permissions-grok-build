# AI Agent Permissions Research Prototype – Context File for LLM Agents

## (Grok Build / Claude / Cursor / Aider Compatible)

**Version:** 1.0.0  
**Date:** 26 May 2026  
**Status:** Research Documentation

---

## 1. PROJECT IDENTITY AND MISSION

**Project Name:** ai-agent-permissions-grok-build-private (research workspace)  
**Core Domain:** Automated prediction of human data-sharing permission preferences for LLM-based agentic systems.  
**Primary Artifact:** Research prototype and evaluation harness accompanying the IEEE S&P 2026 paper "Towards Automating Data Access Permissions in AI Agents" (Wu et al.).

**Mission for Any Agent Working Here:**
You are assisting with a **privacy-sensitive, security-relevant research prototype**. Every change must prioritize correctness, reproducibility, auditability, and minimization of data leakage risk.

**Current Maturity:** Academic research prototype. **NOT** suitable for operational deployment without extensive hardening (see docs/Security-Hardening.md).

---

## 2. REPOSITORY LAYOUT (AUTHORITATIVE)

```
.
├── README.md                          # Primary entry point and overview
├── LICENSE                            # CC BY 4.0 + citation requirement
├── requirements.txt                   # Insecure loose pins – audit before any change
├── queries.json                       # 65 vignette scenarios (ground truth source)
├── docs/
│   ├── SECURITY.md                    # Vulnerability reporting & posture
│   ├── CONTRIBUTING.md                # Contribution rules (security review mandatory)
│   └── website.pdf                    # User study interface (MIRA 2049 framing)
├── data/
│   ├── data_types.csv                 # 77 data types
│   ├── user_study.json                # 203 raw anonymized participants
│   ├── processed_dataset.json         # 181 filtered + train/test splits (PRIMARY DATASET)
│   └── README.md
├── src/
│   ├── permission_cf_only.py          # LightGCN CF baseline (TensorFlow + recommenders)
│   ├── permission_ic_only.py          # Pure OpenAI in-context learning baseline
│   ├── permission_ic_cf.py            # HYBRID (main contribution) – requires cf_scores.csv
│   ├── evaluation_utils.py            # Shared metrics, JSON/CSV I/O, threshold logic
│   └── README.md
├── results/                           # Ephemeral outputs (never commit real runs)
│   └── README.md
└── docs/                              # Professional Documentation
    ├── Architecture.md                # Mermaid component + data flow diagrams
    ├── Security-Hardening.md          # NIST 800-53 / STIG / LLM Top 10 mappings + POA&M
    ├── Build-Process.md               # Reproducibility, SBOM, supply chain
    ├── Configuration.md               # Env vars, hard-coded params, future secure baselines
    ├── Deployment.md                  # Current vs. target accredited architecture
    ├── Troubleshooting.md
    └── AI-Agent-Permissions-Context.md  # THIS FILE
```

**Execution Rule:** All three `permission_*.py` scripts are designed to be run with working directory inside `src/`.

---

## 3. PERMISSION MODEL (RESEARCH DEFINITION)

**Four User Responses Collected (per data type per vignette):**
1. "Yes, always share" → binarized positive (1)
2. "Yes, but ask me first" → excluded from CF training
3. "No, but ask me first" → excluded from CF training
4. "No, never share" → binarized negative (0)

**Modeling Task:** Predict the binary decision for held-out (query, data-type) pairs using:
- User bio + demographics (text)
- AI familiarity / trust / privacy importance (structured + text)
- Historical permission decisions (training examples)
- (Hybrid only) Top-K collaborative filtering recommendations from similar users

**Domains:** Health & Fitness, Finance, Shopping, Travel, Work, Entertainment, Social, Smart Home.

**Data Sensitivity:** Even after anonymization (P001–P203), this encodes privacy attitude + demographic correlations. Treat as privacy-sensitive behavioral data.

---

## 4. PIPELINE DEPENDENCIES AND EXECUTION ORDER (CRITICAL)

1. `python3 permission_cf_only.py` → produces `../results/cf_scores.csv` (and metrics)
2. `python3 permission_ic_only.py` → independent
3. `python3 permission_ic_cf.py` → **requires** cf_scores.csv from step 1

**Never** run hybrid before CF. The hybrid script will warn but may produce degraded or empty results.

---

## 5. SECURITY AND COMPLIANCE IMPERATIVES (MANDATORY CONTEXT FOR ALL AGENTS)

**You (the agent) and any code you generate MUST NOT:**
- Suggest or implement direct calls to commercial LLM providers from classified, CUI, or tactical networks.
- Weaken existing (minimal) input validation or logging.
- Introduce new dependencies without triggering `pip-audit`, `bandit`, and supply-chain review.
- Log raw participant bios, full permission histories, or unsanitized LLM prompts/responses.
- Assume that "ask me" responses can be safely binarized without re-evaluating the paper methodology.
- Create any mechanism that would allow an agent to **act** on a predicted "always share" without human confirmation or policy engine.

**Mandatory References (read before editing security-relevant code):**
- [docs/Security-Hardening.md](Security-Hardening.md) – full NIST 800-53, AU/SC/IA/SI/SR gaps, LLM Top 10 mappings
- [docs/Architecture.md](Architecture.md) – especially future target architecture
- [SECURITY.md](SECURITY.md)
- [docs/Configuration.md](Configuration.md)

**When in doubt:** Stop, surface the security implication to the human operator, and cite the specific control family or OWASP LLM item at risk.

---

## 6. KEY TECHNICAL PATTERNS AND GOTCHAS

**Prompt Construction (High Attack Surface):**
- Both IC scripts use f-string concatenation of user-controlled text directly into the LLM prompt.
- Few-shot examples are hard-coded strings (`EXAMPLE_OUTPUTS`).
- JSON extraction is regex + fallback `json.loads` (fragile, injection-prone).

**Future Hardening Direction:** Replace with Pydantic models + structured outputs + guardrail layer + approved gateway.

**Collaborative Filtering Item Format:**
`{query_id}:::{receiver}:::{datatype_cleaned}`  
Example: `0:::Fitness Tracking:::Fitness goal`

**Evaluation Unification:**
All pipelines ultimately produce lists of (participant, query_id, data_type, pred_label, gt_label). Metrics are computed identically in `evaluation_utils.calculate_metrics`.

**Non-Determinism Sources:**
- OpenAI sampling (no explicit temperature=0 in current code)
- LightGCN training (even with seeds)
- Thread scheduling in parallel participant processing

---

## 7. AGENT BEHAVIOR RULES (WHEN WORKING IN THIS WORKSPACE)

1. **Always** surface security or compliance implications before writing code that touches prompts, data handling, LLM clients, logging, or dependencies.
2. **Never** propose committing `.env`, real prediction outputs, or files containing participant text.
3. **Prefer** edits that improve auditability, input validation, or reproducibility.
4. **When editing prompts:** Preserve the exact instruction hierarchy and "IMPORTANT1/2/3" constraints unless you have a documented, reviewed reason.
5. **Document** every material change in the relevant `docs/` file and cross-reference in PR description.
6. **Verify** after changes: at minimum run `pip-audit`, `bandit -r src/`, and confirm all three pipelines still execute without crashing on the research dataset.

---

## 8. QUICK REFERENCE COMMANDS (FOR AGENTS AND HUMANS)

```bash
# From repo root
cd src

# Full research run (requires key for IC/hybrid)
python3 permission_cf_only.py && python3 permission_ic_only.py && python3 permission_ic_cf.py

# Security quick checks
pip-audit -r ../requirements.txt
bandit -r . -ll

# Data sanity
python -c 'import json; ds=json.load(open("../data/processed_dataset.json")); print(len(ds), "participants")'
```

---

## 9. TRANSITION PATH (RESEARCH → ACCREDITED)

Any agent asked to "make this production ready" or "deploy this for high-security environments" **must** first:
- Read docs/Security-Hardening.md in full
- Produce a delta threat model
- Refuse direct OpenAI integration in any non-research context
- Insist on RMF/ATO prerequisites and approved LLM gateway

---

**This file is the primary context for any LLM agent (Grok, Claude, GPT, Cursor, Aider, etc.) operating in this workspace.**

*End of docs/AI-Agent-Permissions-Context.md*
