# Future Work, Gaps, Limitations, and Proposed Improvements
## Extracted from Local PDF: /home/user/Downloads/wu-agentperms-sp26 (3).pdf (and duplicates)
**Paper:** "Towards Automating Data Access Permissions in AI Agents"  
**Authors:** Yuhao Wu, Ke Yang, Franziska Roesner, Tadayoshi Kohno, Ning Zhang, Umar Iqbal  
**Venue:** 2026 IEEE Symposium on Security and Privacy (S&P)  
**Date of local copies:** May 2026 (latest (3) on 26 May)  
**Method:** Clean visual rendering of pages via read_file (image mode) on local file for accurate text (avoiding prior noisy web text extraction artifacts).

Scanned pages: 1-4 (abstract/intro/goals/threat model), 9-11 (prediction model design, evaluation, confidence, coverage, history impact), 12-15 (results analysis, Discussion §6, Conclusion §7, start of refs).

---

## 1. Explicit Summary Statement (Conclusion, p.14)
> "However, challenges remain in **enforcing predictions, improving robustness, and designing usable interfaces**. Overall, this work advances automated permission management and outlines key directions toward its practical deployment."

## 2. Detailed "Towards Usable Permission Management" (Discussion, p.14 — the richest future-work callout)
> "Automated permission management is a multifaceted problem. Our work in this paper focuses on one facet, and other important facets, including **improving the usability of permission management in AI agents, remain challenges and open avenues for future work**. For example, during early use, the assistant may still need to learn a user’s preferences; a user’s preferences may change as their circumstances change (e.g., a previously trusted entity becomes untrusted); and some situations may be fundamentally difficult to predict. Thus, **a full-fledged permission system will need to include not only a permission prediction module, but also UI/UX for engaging the user directly in cases where the predictive model has low confidence or makes a mistake**—for example, **UI/UX for users to make explicit permission decisions, to revoke previously-granted permissions, and to give feedback to the permission assistant**. We believe **there is rich future work to be done on how to design such a hybrid system**."

> "The important contribution of our work here is to start this line of inquiry and to demonstrate that it is feasible: an effective AI permission assistant can substantially reduce the number of decisions that users must be asked to make or evaluate directly, paving the way for a usable and secure permission management system."

## 3. Model Robustness and Limitations (Discussion, p.13-14)
- Natural language interactions are ambiguous → "this remains an open problem for LLMs [45]. Our in-context learning model can be affected by this ambiguity and may make mistakes when processing unclear instructions."
- Mitigation already in their design: "taking **only high-confidence predictions and delegating uncertain data access permissions to users** can help mitigate the model’s robustness issues. This approach pairs predictions with clear controls to make and revoke decisions and to provide feedback, which reduces interruptions for routine cases while allowing human oversight in riskier or uncertain situations."
- Suggestion to extend prior work: info-flow control, limiting LLM text generation, architectures that limit flow between modules ([8],[52],[79],[16],[79]).

- "We believe that such approaches can be extended to support robust permission management in AI agents."

## 4. High-Confidence / Coverage Trade-off & User-in-the-Loop (p.11, §5.2.2)
- "As permission assistants will make predictions to share data on behalf of users, **a high precision and lower FPR may be desired, which requires a compromise on model coverage**. Thus, **in practice, the users may need to be involved in the loop for making data permission decisions**."
- "custom **confidence thresholds could be configured at the granularity of individual users and/or domains**."
- "certain data types show a high degree of variance across users, so they **may also be excluded from predictions to avoid mistakes**."
- Paper reports 94.4% acc at 0.91 thresh for hybrid but only 25.9% coverage (and similar for IC/CF).

## 5. Impact of Limited History / Cold Start (p.11, Table 6 + text)
- Even with 0 history: 66.9% acc.
- 1-4 queries: +10.8% jump.
- "This continuous learning capability can facilitate real-world deployment, i.e., as users naturally generate more permission history over time, the model can iteratively learn from them..."

## 6. Scope Limitations Explicitly Called Out (p.3-4, §3.1 + §3.2)
- Paper **deliberately focuses only on (i) understanding preferences and (ii) learning/predicting them**.
- "(iii) reliably enforcing predicted preferences" left to "prior complementary work [8], [52], [79]".
- "As the implementation and deployment of the permission assistant requires solving unique challenges of its own, we do not consider it in the scope of this paper." (sandboxing, TEE, malicious flow detection, control of LLM instruction generation).

- Threat model assumes permission assistant itself is trustworthy and deployed in scaffolding without direct LLM access to it.

## 7. Other Related Gaps / Improvement Directions (scattered)
- From abstract + p.2: Conventional install-time and (especially) runtime permission models are inadequate for agentic execution (unknown data needs ahead of time; constant prompting destroys the automation value prop and causes fatigue).
- Need for the predictor to handle **previously unseen data types** without retraining (addressed via LLM in-context in their work).
- High intra-user variance in some users/domains/data types makes prediction harder (p.9, 5.3.1); high-variance users show much lower model accuracy.
- "We anticipate a sustained progression in permission modeling for AI agents over the next several years, during which a wide variety of models will be explored. In this paper, we focus more on the implications from our user study results and present our permission assistant as a **proof of concept and/or initial exploration of the design space, rather than a definitive solution**." (p.9)

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
