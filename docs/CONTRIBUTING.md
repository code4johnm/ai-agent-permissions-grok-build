# Contributing Guide

## AI Agent Permissions Research Prototype

**Version:** 1.0.0  
**Date:** 26 May 2026  
**Status:** Research Documentation

---

## 1. PURPOSE

This document establishes contribution standards, security review requirements, and process expectations for anyone extending or modifying the AI Agent Permissions Research Prototype.

---

## 2. CODE OF CONDUCT AND SECURITY-FIRST MINDSET

All contributors must internalize that this codebase deals with **privacy-sensitive behavioral research data** and models that could be integrated into future autonomous systems.

**Core Principles:**
- **Do no harm.** Changes that could increase leakage risk, weaken auditability, or reduce traceability are unacceptable.
- **Security review is mandatory.** No change touching prompt construction, data loading, LLM I/O, dependency updates, or logging is merged without security engineering review.
- **Reproducibility matters.** All changes must preserve or improve the ability to regenerate paper results (within the limits of non-determinism).

---

## 3. HOW TO CONTRIBUTE (RESEARCH PHASE)

1. **Fork or branch** from `main` (or designated research branch).
2. **Create a focused issue** describing the proposed change, its security impact, and traceability to research questions or hardening roadmap.
3. **Develop** in an isolated environment (see docs/Security-Hardening.md).
4. **Test** all three pipelines end-to-end; do not break CF → IC+CF dependency.
5. **Update documentation** (this includes Architecture.md, Security-Hardening.md, Configuration.md, and relevant README sections).
6. **Submit pull request** with:
   - Clear description of functional change
   - Security impact statement (even if "none")
   - Updated metrics comparison (if evaluation behavior changes)
   - Evidence of local `pip-audit` / `bandit` run

**Small / Documentation-Only Changes:** May proceed with lighter review after security self-attestation.

---

## 4. SECURITY REVIEW REQUIREMENTS

**Mandatory Security Review Triggers (Non-Negotiable):**
- Any modification to `create_ic_prompt`, `create_ic_cf_prompt`, or `EXAMPLE_OUTPUTS`
- Changes to data filtering logic or participant selection criteria
- Dependency additions, removals, or version bumps
- New network calls or file I/O patterns
- Logging or error-handling changes that could affect audit completeness
- Any addition of new LLM providers or model families

**Review Artifacts Expected:**
- Threat analysis delta (how does this change the attack surface described in Security-Hardening.md?)
- Updated control traceability (which NIST 800-53 / AI RMF controls are affected?)
- Penetration test or adversarial prompt results (for LLM-related changes)

---

## 5. CODING STANDARDS

- Python 3.9+ compatibility.
- Type hints preferred on all new public functions.
- Structured logging (avoid bare `print` in new code except for researcher-facing progress).
- All LLM responses must pass through strict schema validation (Pydantic in future).
- No new hard-coded secrets or credentials.
- Relative paths only within documented execution context (`src/` as cwd).

---

## 6. DATA AND MODEL GOVERNANCE

- **Never** add new participant-level data without IRB/ethics review documentation.
- **Never** commit files containing real API keys, raw OpenAI responses with participant context, or un-anonymized data.
- Model retraining or new CF embeddings require updated documentation of seed, hyperparameters, and data snapshot SHA.
- Changes that alter ground-truth alignment (e.g., different binarization of "ask" responses) must be accompanied by full re-evaluation and justification against the original paper methodology.

---

## 7. TRANSITION TO ENGINEERING / ACCREDITED FORK

When this prototype transitions from pure research to a program of record or accredited baseline:
- This CONTRIBUTING.md will be superseded by a formal SSDLC contribution policy.
- All contributors will be required to complete appropriate OPSEC, cybersecurity, and (if applicable) AI ethics training.
- A Security Control Assessor (SCA) or equivalent will be added to the approval chain for all PRs.

---

## 8. RECOGNITION

Contributors who materially advance the security posture or scientific validity of the work will be acknowledged in future revisions of the documentation and (where appropriate) in subsequent publications or transition reports.

---

*End of CONTRIBUTING.md*
