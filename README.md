# AI Agent Permissions Research Prototype

## Secure Permission Inference Framework for LLM-Based Agentic Systems

**Version:** 1.0.0  
**Date:** 26 May 2026  
**Status:** Research Documentation (Not an Official Government Product)

---

**Important Notice**  
This is independent research documentation for an academic prototype. It is **not** an official U.S. government, Department of Defense, or Department of War product. References to security standards (NIST, STIGs, etc.) are provided as best-practice guidance only.

## 1. PURPOSE

This document provides the authoritative entry point and system-level description for the **AI Agent Permissions Research Prototype**. The prototype implements and evaluates automated data access permission prediction mechanisms for LLM-based autonomous agents.

The system addresses a critical security and operational requirement in future agentic AI deployments: the ability to predict and enforce user-specific data-sharing preferences at machine speed while maintaining traceability, auditability, and alignment with human intent.

**Primary Objectives:**
- Evaluate hybrid machine learning + large language model approaches for permission decision automation.
- Provide reproducible baselines (Collaborative Filtering, In-Context Learning, and Hybrid) against a rigorously collected human-subject ground truth dataset.
- Establish a foundation for future integration into secure, RMF-accredited agent permission guardrails in tactical and enterprise environments.

**WARNING:** This is a **RESEARCH PROTOTYPE** developed under academic auspices (IEEE S&P 2026). It has **NOT** completed Risk Management Framework (RMF) assessment, Security Technical Implementation Guide (STIG) hardening, or Authority to Operate (ATO) processes. It is **NOT AUTHORIZED** for use on classified networks, SABI environments, or operational tactical systems without substantial additional engineering, accreditation, and authorization.

---

## 2. SCOPE AND APPLICABILITY

**Scope:** This repository contains the complete experimental apparatus (data, source code, evaluation harness) described in the associated IEEE Symposium on Security and Privacy 2026 paper.

**Applicability:** This documentation is intended for researchers, security engineers, and developers working on permission systems for AI agents. It may be especially relevant to organizations that must meet high security and privacy standards.

**Target Environments (Future Hardened Variants):**
- Air-gapped tactical edge nodes
- SABI / classified processing enclaves
- Enterprise AI platforms subject to strong security and privacy requirements (e.g., NIST SP 800-53 and CNSSI 1253 overlays)

---

## 3. REFERENCES

**Key Security Standards Referenced (best-practice guidance):**
- NIST SP 800-53, Security and Privacy Controls for Information Systems and Organizations
- CNSSI 1253, Security Categorization and Control Selection for National Security Systems
- NSA Kubernetes Hardening Guide (for any future containerized deployments)
- Relevant Security Technical Implementation Guides (STIGs) for applications, Python, and containers
- NIST AI Risk Management Framework (AI RMF 1.0) and Generative AI Profile
- OWASP LLM Top 10 (2025) for agentic/LLM-specific threat modeling

**Technical References:**
- Wu et al., "Towards Automating Data Access Permissions in AI Agents," 2026 IEEE Symposium on Security and Privacy (SP), doi:10.1109/SP63933.2026.00018
- arXiv:2511.17959

---

## 4. SYSTEM OVERVIEW

The prototype consists of three experimental permission inference pipelines plus shared evaluation utilities, operating against a ground-truth dataset derived from a 203-participant (181 filtered) vignette-based user study.

**Core Components:**
- **Data Layer:** Anonymized user study responses, 77 data type catalog, 65 query scenarios across 8 domains.
- **CF-Only Baseline:** LightGCN graph neural collaborative filtering (TensorFlow/recommenders).
- **IC-Only Baseline:** Pure in-context learning via OpenAI models (o4-mini / o3-mini).
- **IC+CF Hybrid (Primary Contribution):** LLM reasoning augmented with top-K collaborative filtering scores injected into prompt context.
- **Evaluation Harness:** Unified binary classification metrics (Accuracy, Precision, Recall, F1, FPR, FNR) with threshold optimization.

**Permission Model (Research Definition):**
Four-level user preference collected per data type per scenario:
1. "Yes, always share"
2. "Yes, but ask me first"
3. "No, but ask me first"
4. "No, never share"

For modeling, binarized to share (1) / never-share (0). "Ask" responses excluded from training in CF pipeline per paper methodology.

See [docs/Architecture.md](docs/Architecture.md) for detailed data flows and component diagrams.

---

## 5. SECURITY CONSIDERATIONS AND KNOWN LIMITATIONS

**Current Security Posture:** Research-grade only. Multiple high-severity gaps exist for any production or high-security use.

**Key Risks (Non-Exhaustive):**
- **Third-Party Data Exfiltration:** All IC/IC+CF paths transmit user bios, AI experience profiles, full permission histories, and query semantics to OpenAI. This violates data sovereignty and CUI/ classified handling requirements.
- **Prompt Injection & Data Poisoning:** User-controlled history and query text are concatenated directly into LLM prompts with minimal escaping or separation. No guardrails, output validation, or constitutional AI layers.
- **Supply Chain:** Loose version pinning in requirements.txt; heavy dependencies (TensorFlow, recommenders) introduce substantial attack surface.
- **No Audit Trail:** Logging is informational only; no tamper-evident security event logging meeting AU-2 / AU-3 controls.
- **Secrets Management:** Relies on local .env files. Inadequate for production (violates IA-5, SC-28).
- **Lack of Input Validation & Output Sanitization:** JSON parsing from LLM responses uses regex fallbacks; no schema enforcement or content filtering.
- **Privacy of Study Data:** Although IRB-anonymized, the dataset encodes highly sensitive privacy attitude + demographic correlations. Mishandling could re-identify or reveal behavioral patterns.

**Mandatory Mitigations Before Any Operational Consideration:**
See [docs/Security-Hardening.md](docs/Security-Hardening.md) for detailed control mappings (NIST 800-53), hardening procedures, and a prioritized remediation roadmap.

**Accreditation Status:** 
- RMF Step 1 (Categorize): Not performed.
- RMF Step 2–6: Not initiated.
- No SSP, no SAR, no POA&M, no ATO.

**Recommendation:** The artifacts contain privacy-sensitive research data. Any integration into production or high-security systems requires additional engineering, review, and hardening.

---

## 6. QUICK START (RESEARCH USE ONLY)

**Prerequisites:**
- Python 3.9+
- OpenAI API key (IC and hybrid paths only)
- Sufficient local compute for LightGCN training (GPU recommended for speed)

**Installation (Development / Research Workstation):**

```bash
git clone <repository-url>
cd ai-agent-permissions-grok-build-private

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Environment:**

```bash
cp .env.example .env   # if template exists; otherwise create manually
# Edit .env:
OPENAI_API_KEY=sk-...
OPENAI_MODEL=o4-mini
```

**Execution Order (from src/):**

```bash
cd src

# 1. CF baseline (no API key required)
python permission_cf_only.py

# 2. IC-only baseline (requires API key)
python permission_ic_only.py

# 3. IC+CF hybrid (requires cf_scores.csv + API key)
python permission_ic_cf.py
```

All outputs land in `../results/`.

**Strong Recommendation:** Never execute on systems containing CUI, PII, or classified data. Use isolated research VMs or containers with egress controls.

---

## 7. REPOSITORY STRUCTURE

```
ai-agent-permissions-grok-build-private/
├── README.md                          # Primary entry point and overview
├── LICENSE                            # CC BY 4.0 (research data)
├── requirements.txt                   # Python dependencies
├── queries.json                       # 65 vignette scenarios + ground truth metadata
├── docs/
│   ├── SECURITY.md                    # Vulnerability reporting & posture
│   ├── CONTRIBUTING.md                # Contribution rules (security review mandatory)
│   └── website.pdf                    # User study interface screenshots
├── data/
│   ├── README.md
│   ├── data_types.csv                 # 77 data types with frequency
│   ├── user_study.json                # Raw anonymized responses (203 participants)
│   └── processed_dataset.json         # Filtered 181-participant dataset with train/test splits
├── src/
│   ├── README.md
│   ├── permission_cf_only.py          # LightGCN CF baseline
│   ├── permission_ic_only.py          # Pure LLM in-context baseline
│   ├── permission_ic_cf.py            # Hybrid (main research contribution)
│   └── evaluation_utils.py            # Shared metrics & I/O
├── results/                           # Generated artifacts (gitignored in operational use)
│   └── README.md
└── docs/                              # Professional Documentation
    ├── Architecture.md                # System & data flow architecture (Mermaid)
    ├── Security-Hardening.md          # Security hardening guidance and gap analysis
    ├── Build-Process.md               # Reproducibility, SBOM, supply chain
    ├── Configuration.md               # Secure configuration baselines
    ├── Deployment.md                  # Current execution model and future considerations
    ├── Troubleshooting.md
    └── AI-Agent-Permissions-Context.md # Context file for LLM coding agents (Grok Build, etc.)
```

See individual `docs/` artifacts for detailed specifications.

---

## 8. DATA HANDLING AND PRIVACY

All participant data has been anonymized per IRB protocol (Prolific IDs replaced with P001–P203). No direct PII remains.

**Data Sensitivity (Research Context):** The dataset contains privacy-sensitive behavioral research responses. Handle with appropriate care even though it has been anonymized.

**Handling Requirements (Even in Research Use):**
- Store on encrypted volumes.
- Restrict access via least-privilege.
- Do not merge with external datasets that could enable re-identification.
- When transmitting (e.g., for collaboration), use approved channels only.

---

## 9. COMPLIANCE AND ACCREDITATION STATUS

**Current State:** Not suitable for production or high-security environments without substantial additional work.

**Planned / Required for Future Variants:**
- Full RMF package (SSP, control implementation descriptions, SAR, POA&M)
- STIG checklists (Python Application, Container if applicable)
- Supply chain attestation (SLSA Level 2+, signed SBOM)
- LLM/GenAI-specific controls per emerging best practices (prompt guardrails, output filtering, provenance)
- Formal threat model (STRIDE + MITRE ATLAS for AI)
- Continuous monitoring & logging architecture meeting SI-4 / AU family controls

See [docs/Security-Hardening.md](docs/Security-Hardening.md) for gap analysis and prioritized roadmap.

---

## 10. CITATION AND ACKNOWLEDGMENT

When referencing this work or using the data/code, cite the primary research publication:

```bibtex
@inproceedings{wu2026automating,
  title={{Towards Automating Data Access Permissions in AI Agents}},
  author={Wu, Yuhao and Yang, Ke and Roesner, Franziska and Kohno, Tadayoshi and Zhang, Ning and Iqbal, Umar},
  booktitle={2026 IEEE Symposium on Security and Privacy (SP)},
  pages={336--354},
  year={2026},
  organization={IEEE},
  doi={10.1109/SP63933.2026.00018}
}
```

**Research Team (Original):** Yuhao Wu (WUSTL), Ke Yang (UCI), Franziska Roesner (UW), Tadayoshi Kohno (Georgetown), Ning Zhang (WUSTL), Umar Iqbal (WUSTL).

**Documentation Note:** This documentation set was created to provide professional-grade, security-focused guidance for the research artifact, drawing on widely recognized cybersecurity standards and best practices.

---

*End of README.md*
