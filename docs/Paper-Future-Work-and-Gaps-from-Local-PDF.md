# Paper Future Work, Gaps & Limitations (Condensed)

**Source:** Clean visual extraction from local `~/Downloads/wu-agentperms-sp26 (3).pdf` (19 pages, Wu et al., IEEE S&P 2026).

**Note:** Several items listed below are now directly addressed in this repository:
- `src/permission_assistant.py` implements the "usable hybrid system" (high-confidence auto + user defer for low confidence, revocation, live feedback, 4-option choices).
- Robust LLM output parsing + confidence-threshold evaluation in `evaluation_utils.py`.
- See inline quotes in `permission_assistant.py` and the implementation mapping at the bottom of this file.

---

## Key Statements from the Paper

**Conclusion (p.14):**
> "challenges remain in **enforcing predictions, improving robustness, and designing usable interfaces**."

**Towards Usable Permission Management (p.14):**
The paper calls for a full system that includes not only prediction but also:
- UI/UX for low-confidence cases and model mistakes
- Ability to make explicit decisions, revoke grants, and give feedback
- Handling of early-use learning, preference drift, and fundamentally hard-to-predict situations

It explicitly states there is "rich future work" needed on designing such a **hybrid system**.

**Model Robustness (p.13-14):**
- Natural language is ambiguous; this "remains an open problem for LLMs".
- Their recommended mitigation: **high-confidence predictions only** + delegating uncertain cases to users.
- Suggest extending prior work on information-flow control and limiting LLM instruction generation ([8], [52], [79]).

**Other Notable Gaps Called Out**
- Paper deliberately scoped to (i) understanding preferences and (ii) prediction only. "(iii) reliably enforcing" left to complementary work.
- Conventional install-time and runtime permission models are inadequate for the agentic paradigm.
- High user variance on certain data types makes accurate prediction difficult.
- The work is presented as "a proof of concept and/or initial exploration of the design space, rather than a definitive solution."

---

**Implementation Status (this repo):**  
The `permission_assistant.py` demo + confidence-aware evaluation harness were added specifically to address the "designing usable interfaces" and "high-confidence + user in the loop" directions from the paper. Enforcement and full production hardening remain out of scope (see the dedicated Security-Hardening and Compliance-Gaps documents).

For the full verbatim extracts, refer to the original local PDF or the earlier detailed version of this file (git history).

- Release of data + code "To foster future research" (p.2).

## 8. Meta-Review (p.19, acceptance notes)
- Positions the work as establishing "a New Research Direction".
- "This paper is one of the first to investigate the problem of automating permission management for AI agents."

---

## Mapping to Implemented Code (in this repo as of 2026)
(See also the changes in src/permission_assistant.py, evaluation_utils.py, README updates, and the pre-existing compliance/Architecture future-state diagrams.)

The local clean PDF confirms the prior implementation work directly targets the quoted items above.

**Already addressed in this grok-build:**
- `src/permission_assistant.py`: Full interactive hybrid demo of the "usable hybrid system" (high-conf auto + explicit defer to the 4 study options on low conf, revocation UI, live feedback that mutates session history for drift/early-use simulation, full audit log of every decision with source/provenance/rationale). Exactly matches the long "UI/UX for low confidence... revoke... give feedback" + "during early use... preferences may change" + "human oversight in riskier or uncertain situations" paragraphs.
- Confidence threshold support + coverage metrics in evaluation_utils.py (plus pretty printer) → directly enables the 94.4% high-conf / reduced-coverage points and "custom confidence thresholds" + "users may need to be involved in the loop".
- Robust multi-strategy + (optional) Pydantic JSON extraction in the IC/hybrid paths and new utils → addresses the "natural language interactions can be ambiguous... may make mistakes when processing unclear instructions" + "improving robustness".
- Existing docs (Architecture future target with Guard + Policy + Audit, Deployment tiers, Compliance-Gaps roadmap, Security-Hardening) already sketch the enforcement (iii) path and many of the "unique challenges of its own" left out of the paper scope.

**Minor remaining opportunities visible from this clean scan (low priority for this task):**
- Explicit per-domain or per-user threshold configuration UI (the demo has a global const; easy extension).
- More sophisticated history drift simulation or revocation propagation example.
- Direct integration of the assistant with the saved cf_scores + real per-participant CF lookup in the demo (currently mock + optional full LLM).
- A non-demo library class that the three research scripts could optionally call for single-query inference.

This catalog was generated directly from visual page renders of the local PDF for maximum fidelity.

*End of catalog (generated after tool-based visual scan of local ~/Downloads/wu* files).*
