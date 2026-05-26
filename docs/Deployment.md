# Deployment Guide

## AI Agent Permissions Research Prototype

**Version:** 1.0.0  
**Date:** 26 May 2026  
**Status:** Research Documentation

---

**WARNING:** There is **no supported deployment model** for this research prototype in any operational or high-security environment. This document describes the current (unsupported) execution model and the **required future deployment architecture** for production use.

## 1. CURRENT EXECUTION MODEL (RESEARCH ONLY)

**Environment:** Developer workstation or isolated research VM/container.

**Deployment Steps:** See [README.md](../README.md#6-quick-start-research-use-only) and [docs/Build-Process.md](Build-Process.md).

**Constraints:**
- Requires local Python 3.9+
- OpenAI API key for two of three pipelines (data exfiltration risk)
- No high-availability, no scaling, no monitoring
- Results are local files only
- No authentication or authorization layer

**Prohibited Environments:**
- Any system containing CUI, PII, or classified data
- Shared/multi-tenant research clusters without strict network egress controls
- Production AI agent platforms
- Tactical edge devices

---

## 2. TARGET DEPLOYMENT ARCHITECTURE (ACCREDITED)

See the future-state diagram in [docs/Architecture.md](Architecture.md#7-future-target-architecture-accredited-operational-variant).

**Core Principles for Operational Deployment:**
- **Zero direct commercial LLM calls** from within any high-security or air-gapped environment.
- **Permission decisions are enforced actions**, not offline research predictions.
- **Full provenance and audit** for every decision (who, what query, what data types, what model version, what CF contribution, human override if any).
- **Human-in-the-loop or policy-based override** for all "always share" decisions in sensitive domains (Health, Finance, Smart Home, etc.).

**Deployment Tiers (Illustrative):**

| Tier | Target Environment | LLM Backend | CF Backend | Guardrail Enforcement | Audit Destination |
|------|--------------------|-------------|------------|-----------------------|-------------------|
| Research | Isolated workstation | OpenAI (current) | Local LightGCN | None | Local files |
| Pilot | IL5 / GovCloud dev | Approved gateway | Model registry (signed) | Prompt filter + schema | Centralized SIEM |
| Tactical Edge | Disconnected / DIL node | On-prem quantized LLM (vLLM) | Edge CF model (ONNX) | Local guard + policy store | Local tamper-evident log + sync on reconnect |
| Enterprise / High-Security | Hardened AI platform | Approved private LLM service | Centralized CF service | API gateway + mTLS | Enterprise SIEM + immutable store |

---

## 3. DEPLOYMENT PREREQUISITES (FUTURE)

**Mandatory Before Any Pilot Deployment:**
1. Completed RMF package with ATO (or Interim ATO) including AI overlay controls.
2. Approved LLM gateway with injection detection, DLP, and response validation.
3. Signed and attested container images + SBOM.
4. Secrets management integration (Vault or equivalent) – no long-lived keys in pods.
5. Network policy / service mesh enforcing egress only to approved LLM gateway.
6. Independent adversarial ML assessment (prompt injection, model extraction, membership inference on user embeddings).
7. Updated threat model and POA&M with residual risk accepted by AO.

**Kubernetes / Container Platform Requirements (when applicable):**
- Platform One / Iron Bank hardened images or equivalent
- Kyverno or OPA Gatekeeper policies enforcing:
  - No privileged containers
  - Read-only root FS
  - No hostPath mounts for data
  - Image signature verification (cosign)
- NetworkPolicy restricting egress to LLM gateway only
- Falco / Tetragon runtime threat detection rules for anomalous Python/LLM behavior

---

## 4. DATA PLANE vs. CONTROL PLANE (FUTURE)

**Data Plane (High Volume, Low Latency):**
- Permission Guardrail Service receives agent query + user context + candidate data types
- Returns structured decision + confidence + rationale + provenance hash
- Must meet latency SLOs of the calling agent (sub-second for tactical)

**Control Plane (Low Volume, High Assurance):**
- Model update pipeline (signed artifacts only)
- Policy / threshold tuning with human approval
- Audit log archival and compliance reporting
- Incident response hooks (e.g., rapid revocation of a compromised model version)

---

## 5. ROLLBACK AND INCIDENT RESPONSE

**Future Requirements:**
- Model version pinning in every decision record
- Ability to instantly disable a model version or CF index via control plane
- Canary / shadow mode deployment for new models (compare predictions without enforcement)
- Human override API with full audit of overrides

---

## 6. CURRENT LIMITATIONS SUMMARY

| Capability | Current State | Required for Operational Use |
|------------|---------------|------------------------------|
| Packaging | None (loose .py files) | Signed container + Helm chart or equivalent |
| Secrets | .env file | Vault + short-lived credentials |
| LLM Backend | Direct commercial | Approved air-gapped or IL5/6 gateway with guardrails |
| Scaling | Single process | Horizontal via Kubernetes HPA + queue |
| Observability | print() + basic logger | Structured audit + metrics + tracing (OpenTelemetry) |
| Authorization | None | Strong PKI or equivalent / mTLS + ABAC policy engine |
| Update Mechanism | Manual git pull | GitOps (Flux/Argo) with signed commits + image verification |

---

*End of docs/Deployment.md*
