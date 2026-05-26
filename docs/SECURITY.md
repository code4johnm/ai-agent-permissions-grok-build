# Security Policy

## AI Agent Permissions Research Prototype

**Version:** 1.0.0  
**Date:** 26 May 2026  
**Status:** Research Documentation

---

## 1. SUPPORTED VERSIONS

This repository is a **research prototype** and is not currently receiving security updates in the manner of production software.

| Version | Supported          | Notes |
| ------- | ------------------ | ----- |
| 1.0.0   | Research use only  | Current academic artifact; hardening required for production or high-security use |

**No warranty or ongoing maintenance commitment** is provided for operational security.

---

## 2. REPORTING A VULNERABILITY

**For vulnerabilities discovered in the research code or data handling:**

Because this is an academic research artifact (originally published under IEEE S&P 2026), vulnerabilities should be reported to the original research team contacts listed in the paper and cross-referenced in [README.md](README.md).

**For high-security or regulated environments:**
- Report through official channels (e.g., service CERT, program security officer, or vulnerability disclosure program if this prototype is ever adopted by a program of record).
- **Do not** open public GitHub issues containing sensitive details, exploit code, or data handling concerns.

**What to include in a report:**
- Description of the vulnerability and affected component(s)
- Steps to reproduce (sanitized; do not include real API keys or participant data)
- Potential impact assessment (data exposure, prompt injection, supply chain, etc.)
- Suggested remediation (if known)

**Response Commitment (Research Context):** The original academic team has no formal SLA. For any future accredited fork, a 90-day coordinated disclosure policy will be adopted.

---

## 3. KNOWN SECURITY LIMITATIONS (RESEARCH PROTOTYPE)

**This software must NOT be used in any environment processing CUI, PII, classified information, or mission-critical data without complete re-architecture and accreditation.**

**Documented High-Risk Areas (see docs/Security-Hardening.md for full analysis):**
- Direct transmission of user privacy profiles and query semantics to commercial third-party LLM providers (OpenAI).
- Absence of prompt injection defenses or output guardrails.
- Loose dependency management with no SBOM or reproducible builds.
- Lack of audit logging meeting NIST AU controls.
- Use of local `.env` files for long-lived API credentials.
- No input validation or cryptographic integrity on model artifacts and generated scores.

**Immediate Operational Restrictions:**
- Execute only on isolated research systems with no production data.
- Never allow egress to commercial LLM endpoints from classified or CUI networks.
- Treat all generated predictions and study data as privacy-sensitive even after anonymization.

---

## 4. SECURE DEVELOPMENT REQUIREMENTS (FUTURE)

Any engineering team intending to transition this research into a program of record **shall**:
1. Adopt a formal Secure Software Development Lifecycle (SSDLC) aligned with recognized secure development practices and software assurance policies.
2. Produce appropriate security documentation and risk assessment artifacts for the target environment.
3. Implement continuous integration with signed commits, SBOM generation, and container/image signing.
4. Replace all commercial LLM calls with approved on-premises or private LLM infrastructure that enforces prompt/response filtering and full audit.
5. Achieve relevant STIG compliance (Python, Container, Application Security and Development).
6. Conduct independent penetration testing and adversarial ML assessment (MITRE ATLAS).

---

## 5. CONTACT

For security policy questions regarding this documentation set:
- Refer to the preparing Senior Software Systems Engineer via project channels.
- For the underlying research: Contact the authors via the affiliations listed in the IEEE paper citation.

*End of SECURITY.md*
