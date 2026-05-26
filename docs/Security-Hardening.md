# Security Hardening and Compliance Guide

## AI Agent Permissions Research Prototype

**Version:** 1.0.0  
**Date:** 26 May 2026  
**Status:** Research Documentation

---

This document provides security hardening guidance and gap analysis for the AI Agent Permissions Research Prototype. It draws on widely recognized cybersecurity standards and best practices (including NIST SP 800-53, CNSSI 1253, NSA Kubernetes guidance, relevant STIGs, the NIST AI Risk Management Framework, and the OWASP LLM Top 10) as useful references for high-assurance environments. It is not an official government document.

## 1. PURPOSE

This document provides a comprehensive security hardening roadmap, control mapping, and gap analysis for the AI Agent Permissions Research Prototype. It identifies current deficiencies against widely recognized cybersecurity standards and best practices, and outlines steps that would be prudent before considering integration into any production or high-security system.

**Scope:** All code, data, build artifacts, execution environments, and future deployment targets associated with this prototype.

**Intended Audience:** Security Control Assessors (SCA), Authorizing Officials (AO), System Security Engineers, AI/ML platform teams, and program managers evaluating this technology for mission use.

---

## 2. EXECUTIVE SUMMARY – CURRENT SECURITY POSTURE

**Overall Assessment:** Research-grade prototype. **HIGH RISK** for any environment handling CUI, PII, or mission data. Multiple critical and high control deficiencies exist across the NIST 800-53 control families.

**Primary Risk Vectors:**
1. **Uncontrolled Third-Party Data Sharing (OpenAI)** – All in-context learning paths exfiltrate user behavioral profiles and query semantics to commercial LLM providers. Violates SC-7, SC-8, AC-17, MP-7, and data sovereignty requirements.
2. **Prompt Injection & Adversarial ML** – Direct concatenation of untrusted user history and query text into LLM system prompts with no isolation, no guardrails, and no output validation. Maps to multiple LLM Top 10 items (Prompt Injection, Data Leakage, etc.).
3. **Supply Chain Compromise** – Loose dependency pinning; no SBOM; no reproducible builds; no signed artifacts. High risk under SSDF and SLSA expectations.
4. **Insufficient Audit & Accountability** – Only basic application logging. No security-relevant event capture, no integrity protection of logs, no centralized collection.
5. **Inadequate Secrets & Credential Management** – .env file pattern violates IA-5(1), SC-28, and AC-6.
6. **Absence of RMF Artifacts** – No System Security Plan (SSP), no control traceability matrix, no risk assessment, no POA&M.

**Residual Risk if Deployed Without Remediation:** Very High. The current implementation is likely to result in unauthorized disclosure of privacy-sensitive data, model poisoning, or supply-chain issues if used without substantial additional hardening.

---

## 3. NIST SP 800-53 / CNSSI 1253 CONTROL MAPPING AND GAPS

Control families are prioritized by current exposure. Each entry includes:
- **Current Implementation Status**
- **Gap Description**
- **Required Hardening / Mitigation**
- **Target Compliance Level** (for future accredited baseline)

### 3.1 Access Control (AC) Family

| Control | Status | Gap | Required Action |
|---------|--------|-----|-----------------|
| AC-2 Account Management | Not Implemented | No user accounts or identity model (local scripts only) | Implement least-privilege service accounts with MFA for any future service wrapper. |
| AC-3 Access Enforcement | Not Implemented | All code paths execute with full local user privileges | Containerize with read-only root filesystem, drop capabilities, seccomp profiles (STIG Container V2R1). |
| AC-6 Least Privilege | Not Implemented | Scripts read/write arbitrary paths; no sandboxing | Enforce via Kubernetes SecurityContext (runAsNonRoot, allowPrivilegeEscalation: false) and AppArmor/SELinux profiles. |
| AC-17 Remote Access | N/A (local) | Future remote execution paths undefined | Require mutual TLS + certificate pinning; disallow direct OpenAI calls from classified enclaves. |

### 3.2 Audit and Accountability (AU) Family – CRITICAL GAP

| Control | Status | Gap | Required Action |
|---------|--------|-----|-----------------|
| AU-2 Event Monitoring | Partial (print/logger) | Only informational logs; no security-relevant events (failed auth, prompt anomalies, data access) | Implement structured JSON logging of all permission decisions, LLM calls (sanitized), file I/O on sensitive data. Route to SIEM. |
| AU-3 Content of Audit Records | Not Implemented | No timestamps with source, no unique IDs, no outcome indicators | Add tamper-evident fields (HMAC or signed log entries). Meet AU-3(1) requirements. |
| AU-6 Audit Review | Not Implemented | No review, analysis, or alerting capability | Add local anomaly detection on FPR/FNR drift and permission override rates. |
| AU-9 Protection of Audit Information | Not Implemented | Logs stored in plaintext results/ directory | Write logs to append-only volume or remote syslog with integrity protection (AU-9(3)). |
| AU-12 Audit Generation | Not Implemented | No selective audit of permission decisions | Log every predicted permission with participant/query hash (no PII), model version, CF score contribution, and final label. |

**Immediate Action:** Add a `security_audit.py` module before any further development.

### 3.3 Security Assessment and Authorization (CA) Family

| Control | Status | Gap | Required Action |
|---------|--------|-----|-----------------|
| CA-2 Control Assessments | Not Performed | No SCA, no SAR | Commission independent security assessment against this document's hardening requirements. |
| CA-5 Plan of Action and Milestones | Not Initiated | No POA&M | Develop POA&M tracking all items in Section 6. |
| CA-6 Authorization | Not Initiated | No ATO-equivalent review | A full security review and risk assessment package would be required for production use. Categorize according to the sensitivity of the data and environment. |

### 3.4 Configuration Management (CM) Family

| Control | Status | Gap | Required Action |
|---------|--------|-----|-----------------|
| CM-2 Baseline Configuration | Not Implemented | No documented secure baseline | Create hardened Python runtime image + locked requirements.txt with hashes. |
| CM-3 Configuration Change Control | Not Implemented | No change control board, no signed commits enforced | Mandate signed commits (GPG) + mandatory security review for all PRs touching prompt construction or data handling. |
| CM-6 Configuration Settings | Not Implemented | Hard-coded paths, model names, no runtime security knobs | Externalize all parameters via signed config (e.g., Kubernetes ConfigMap + validation webhook). |
| CM-7 Least Functionality | Partial | Full Python + TF runtime present | Build minimal runtime using distroless or Chainguard Python images; remove compilers, shells. |
| CM-8 System Component Inventory | Not Implemented | No SBOM | Generate SPDX or CycloneDX SBOM on every build (see Build-Process.md). |

### 3.5 Identification and Authentication (IA) Family

| Control | Status | Gap | Required Action |
|---------|--------|-----|-----------------|
| IA-2 Identification and Authentication (Organizational Users) | Not Implemented | No authentication layer | For any service-ized deployment, require strong authentication (e.g., certificates, hardware tokens, or approved federation). |
| IA-5 Authenticator Management | Partial (API key) | Raw OpenAI key in environment | Migrate to short-lived tokens from an approved secrets manager (e.g., HashiCorp Vault or equivalent with FIPS-validated backends). Never persist long-lived commercial LLM keys in high-security environments. |
| IA-5(1) Password-Based Authentication | N/A | .env pattern is equivalent to plaintext password storage | Prohibit .env in any accredited environment. |

### 3.6 System and Communications Protection (SC) Family – CRITICAL

| Control | Status | Gap | Required Action |
|---------|--------|-----|-----------------|
| SC-7 Boundary Protection | Not Implemented | Direct egress to api.openai.com from any execution host | Future deployments must proxy all LLM traffic through an approved, monitored, content-filtering gateway with DLP and prompt logging (SC-7(5), SC-7(8)). |
| SC-8 Transmission Confidentiality and Integrity | Not Implemented | OpenAI SDK uses TLS 1.2+; however, no certificate pinning or mutual auth | Implement certificate pinning for OpenAI endpoints (or replacement approved LLM gateway). |
| SC-12 Cryptographic Key Establishment and Management | Not Implemented | No local cryptographic material | For future on-prem models (Llama-3.1/3.2 via vLLM/TGI), use FIPS 140-3 validated modules. |
| SC-28 Protection of Information at Rest | Partial (OS level) | Study data and results stored unencrypted at rest on developer workstations | Mandate LUKS/BitLocker + file-level encryption (gocryptfs or equivalent) for all research data stores. |
| SC-39 Process Isolation | Not Implemented | All Python scripts run in same address space as user shell | Containerize with separate PID namespaces; use gVisor or Kata Containers for high-assurance workloads. |

### 3.7 System and Information Integrity (SI) Family

| Control | Status | Gap | Required Action |
|---------|--------|-----|-----------------|
| SI-4 Information System Monitoring | Not Implemented | No runtime behavioral monitoring | Deploy Falco or eBPF-based detection for anomalous file access or unexpected network connections during execution. |
| SI-7 Software, Firmware, and Information Integrity | Not Implemented | No code signing, no runtime integrity measurement | Sign all Python wheels + container images with cosign; verify at admission (Kubernetes) or runtime. |
| SI-10 Information Input Validation | Partial (basic JSON) | LLM output parsed with regex; no Pydantic or JSON Schema enforcement | Replace ad-hoc extraction with strict Pydantic v2 models + re-prompt on validation failure. |
| SI-11 Error Handling | Partial | Stack traces may leak paths and library versions | Sanitize all error messages returned to users or logs; implement circuit breakers on repeated LLM failures. |

### 3.8 Supply Chain Risk Management (SR) Family

| Control | Status | Gap | Required Action |
|---------|--------|-----|-----------------|
| SR-2 Supply Chain Risk Management Plan | Not Implemented | No SCRM plan | Develop SCRM plan per NIST SP 800-161 Rev. 1; assess recommenders, TensorFlow, and OpenAI as critical suppliers. |
| SR-3 Supply Chain Controls and Processes | Not Implemented | No provenance attestation | Require SLSA provenance for all build artifacts. |
| SR-4 Provenance | Not Implemented | No build attestation | Integrate cosign + SLSA GitHub Action (or equivalent) in future CI. |
| SR-5 Acquisition Strategies | Not Implemented | requirements.txt allows version drift | Pin all dependencies to exact versions + hash; regenerate lockfile on every build. |

### 3.9 AI / LLM Specific Controls (Emerging – NIST AI RMF and Related Guidance)

**Mapped to OWASP LLM Top 10 (2025) and NIST Generative AI Profile:**

- **LLM01:2025 Prompt Injection** – **CRITICAL**. User permission history and queries are injected verbatim. No delimiters, no sandboxed tool use, no instruction hierarchy.
  - **Mitigation:** Adopt instruction hierarchy (OpenAI), use LangChain/LlamaIndex guardrails or NVIDIA NeMo Guardrails, implement output filtering with Llama-Guard or equivalent.
- **LLM02:2025 Sensitive Information Disclosure** – **HIGH**. Full user privacy profiles sent to OpenAI.
  - **Mitigation:** Local or approved private on-prem LLM only for any operational path; synthetic data generation for training; differential privacy on CF embeddings.
- **LLM06:2025 Excessive Agency** – N/A today (prediction only, no action execution), but future agent integration would require strict tool scoping and human-in-loop for all "share" decisions.
- **LLM08:2025 Vector and Embedding Weaknesses** – Future risk if retrieval-augmented permission memory is added.
- **Model Extraction / Membership Inference:** CF model and user embeddings could leak individual privacy preferences via repeated queries.

**Additional Considerations for High-Security Environments:**
- All permission decisions should be explainable (current hybrid provides partial rationale via CF scores + LLM reasoning).
- Human oversight is strongly recommended for any automated "always share" decisions in operational systems.
- Continuous monitoring for distribution shift in user permission behavior is advisable.

---

## 4. HARDENING PROCEDURES (PRIORITIZED)

### Phase 0 – Immediate (Before Any Further Experimentation)
1. Create isolated research VM or container with no persistent credentials.
2. Disable internet egress except via authenticated proxy (if required for OpenAI).
3. Encrypt all local storage containing data/ or results/.
4. Add `.env` and `results/` to `.gitignore` (verify).
5. Generate minimal SBOM using `pip-audit` + `syft`.

### Phase 1 – Research Hardening (3–6 months)
- Replace OpenAI direct calls with approved gateway that performs:
  - Prompt sanitization / injection detection
  - PII / sensitive data redaction
  - Response schema enforcement
  - Full prompt + response logging (sanitized)
- Pin and hash all Python dependencies; produce reproducible wheels.
- Add Pydantic models for all LLM I/O.
- Implement structured security audit logging.
- Containerize using hardened base image (Chainguard Python or Iron Bank Python).
- Add Trivy / Grype scanning in local build.

### Phase 2 – Pre-Accreditation Engineering (6–18 months)
- Migrate permission inference to approved on-premises or private LLM infrastructure (e.g., vLLM, TGI, or equivalent with FIPS-validated stack where required).
- Re-implement CF component using approved ML platform (e.g., with model registry, signed artifacts).
- Develop full SSP and control implementation descriptions.
- Conduct threat modeling workshop (STRIDE + MITRE ATLAS).
- Implement continuous ATO monitoring pipeline.

### Phase 3 – Accredited Baseline
- Complete RMF Steps 2–6.
- Achieve ATO with AI overlay.
- Deploy behind API gateway with mTLS, rate limiting, and decision provenance.
- Integrate with enterprise identity (PKI) and secrets management.
- Pass relevant STIGs + SCAP validation.

---

## 5. DATA CLASSIFICATION AND HANDLING

**Study Data (user_study.json, processed_dataset.json):**
- **Sensitivity:** Privacy-sensitive research data (anonymized user study responses)
- **Handling:** Store encrypted at rest. Access limited to cleared research personnel. No cloud storage without FIPS 140-3 validated encryption + approved provider (e.g., AWS GovCloud, Azure IL5/IL6).
- **Retention:** Per IRB protocol and institutional records schedules. Do not retain longer than required for reproducibility.

**Queries and Model Artifacts:**
- The derived CF embeddings can encode behavioral patterns from the study data – handle with appropriate care.

**Never:**
- Commit `.env` or real API keys.
- Upload dataset to public Hugging Face / GitHub without additional IRB review.
- Merge with commercial or other research datasets without re-identification analysis.

---

## 6. COMPLIANCE GAP SUMMARY AND POA&M CANDIDATES

**Critical (Must Close Before Any CUI Exposure):**
- AU family (audit)
- SC-7 / SC-8 (boundary protection & TLS pinning)
- IA-5 (secrets)
- SI-10 (input/output validation for LLM)
- SR family (supply chain)
- LLM01 / LLM02 prompt & data leakage

**High:**
- CM-2/6/7/8 (configuration & SBOM)
- AC-3/6 (least privilege & container hardening)
- SI-4 / SI-7 (integrity & monitoring)

**Moderate:**
- Full RMF documentation package
- Formal threat model update
- Continuous monitoring architecture

A living POA&M shall be maintained in the project repository (docs/POA&M.md – to be created in v1.1).

---

## 7. TOOLS AND REFERENCES FOR HARDENING

- Static Analysis: `bandit`, `semgrep` (LLM rules), `pip-audit`, `safety`
- Container Scanning: Trivy, Grype, Docker Scout
- SBOM: Syft + Grype, `cyclonedx-bom`
- Supply Chain: cosign, SLSA GitHub generator
- LLM Guardrails: NVIDIA NeMo, Llama-Guard-3, OpenAI Moderation (via gateway)
- Secrets: HashiCorp Vault (FIPS), AWS Secrets Manager (GovCloud)
- Runtime Hardening: gVisor, Kata, Falco, Tetragon

See also:
- NSA "Kubernetes Hardening Guide" (latest)
- Hardened container images from trusted sources (e.g., Iron Bank, Chainguard, or equivalent minimal images)
- CNCF Supply Chain Security White Paper

---

## 8. DOCUMENT MAINTENANCE

This Security-Hardening.md must be reviewed:
- After any change to prompt construction logic or data handling
- Upon release of new STIGs or NIST AI RMF updates
- Prior to any transition from research to engineering phase
- At least annually

**Change History:**
- v1.0.0 (26 May 2026) – Initial professional security hardening baseline created from codebase analysis.

---

**Status:** Research Documentation  
**Handle according to your organization's security policies and applicable standards.**

*End of docs/Security-Hardening.md*
