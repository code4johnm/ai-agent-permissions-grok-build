# Configuration Management and Secure Baselines

## AI Agent Permissions Research Prototype

**Version:** 1.0.0  
**Date:** 26 May 2026  
**Status:** Research Documentation

---

**References:** [README.md](../README.md), [docs/Security-Hardening.md](Security-Hardening.md), [docs/Architecture.md](Architecture.md)

## 1. PURPOSE

This document defines the configuration items, environment variables, runtime parameters, and secure baseline settings for the AI Agent Permissions Research Prototype. It establishes the minimum acceptable configuration for research use and the enhancements that would be prudent for production or high-security deployments.

---

## 2. CONFIGURATION ITEMS

### 2.1 Environment Variables (Current Research Implementation)

| Variable | Required | Default | Description | Security Notes |
|----------|----------|---------|-------------|----------------|
| `OPENAI_API_KEY` | Yes (IC / IC+CF only) | None | Commercial LLM provider credential | **HIGH RISK** – Never store in git, never use in classified/CUI environments. Rotate frequently. Prefer short-lived tokens from approved vault. |
| `OPENAI_MODEL` | No | `o4-mini` | Model identifier passed to OpenAI | Validate against approved model list. Older models (o3-mini-2025-01-31) referenced in paper may be deprecated. |

**Research .env File Template (DO NOT COMMIT):**
```bash
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=o4-mini
```

### 2.2 Hard-Coded Configuration (Requires Hardening)

**LightGCN (permission_cf_only.py):**
- `TOP_K = 5`
- `EPOCHS = 120`
- `BATCH_SIZE = 256`
- `SEED = DEFAULT_SEED` (from recommenders)
- `LIGHTGCN_CONFIG` dict (embed_size, n_layers, lr, decay, etc.)

**IC Pipelines:**
- `MAX_WORKERS = 5`
- `TOP_K = 5` (hybrid only)
- Hard-coded few-shot `EXAMPLE_OUTPUTS` JSON template

**Paths (Brittle):**
- All scripts use relative paths (`../data/`, `../results/`, `../queries.json`)
- No environment-based path override

**Recommendation for v1.1+:** Externalize via Pydantic `BaseSettings` + YAML/JSON config with schema validation and digital signature verification.

### 2.3 Data Configuration

- `data/processed_dataset.json` – 181 participants (filter criterion: ≥5 decisive responses)
- `queries.json` – 65 scenarios, 8 domains
- `data_types.csv` – 77 generic data types

These are **immutable research artifacts**. Any modification invalidates paper results and ground truth alignment.

---

## 3. SECURE BASELINE CONFIGURATION (RESEARCH WORKSTATION)

**Minimum for Responsible Research Use:**

1. **Isolation**
   - Dedicated VM or container with no access to production credentials or data.
   - Full-disk encryption enabled (LUKS/BitLocker/FileVault).

2. **Network**
   - Egress to `api.openai.com` permitted only when running IC/Hybrid (CF pipeline is air-gap safe).
   - DNS filtering + TLS inspection proxy recommended even for research.

3. **Python Environment**
   - Virtual environment (venv) or Conda env per project.
   - `pip install -r requirements.txt` followed immediately by `pip-audit --desc` and `pip check`.
   - Never run as root.

4. **Secrets**
   - `.env` file present only on the isolated workstation.
   - Add `.env` and `results/` to `.gitignore` (verify before every commit).
   - Prefer 1Password / KeePass / approved enterprise vault over plaintext .env for long-term key storage.

5. **Logging**
   - Python `logging` level INFO or higher (current default in IC scripts).
   - Redirect stdout/stderr to timestamped files for reproducibility.

---

## 4. HARDENED CONFIGURATION REQUIREMENTS (PRE-ACCREDITATION)

**Mandatory Changes Before RMF Step 2:**

- **Secrets:** Migrate `OPENAI_API_KEY` usage to:
  - HashiCorp Vault (FIPS 140-3 backend) with short-lived tokens, or
  - Approved secrets management with FIPS-validated backends (e.g., HashiCorp Vault, cloud KMS with FIPS endpoints) and automatic rotation.
- **LLM Endpoint:** Replace direct OpenAI SDK with internal gateway that enforces:
  - Prompt sanitization / injection detection (e.g., via NeMo Guardrails or custom WAF rules)
  - Response schema enforcement + Pydantic validation
  - Full (sanitized) prompt/response logging to immutable audit store
- **Configuration as Code:**
  - All model parameters, thresholds, worker counts, and paths defined in signed YAML/JSON.
  - Runtime validation + checksum verification on load.
- **Feature Flags / Experiment Control:**
  - Add explicit toggles for "enable_cf", "enable_llm", "audit_level" rather than code branches.
- **Resource Limits:**
  - CPU/memory requests + limits when containerized.
  - OpenAI rate-limit backoff already present via tenacity (good); make parameters configurable.

---

## 5. DEPENDENCY CONFIGURATION (SUPPLY CHAIN)

**Current (Insecure for High-Security Use):**
```txt
pandas>=2.0.0
numpy>=1.24.0,<2.0.0
scikit-learn>=1.0.0
tensorflow>=2.13.0
openai>=1.0.0
recommenders==1.2.1
python-dotenv>=1.0.0
tqdm>=4.65.0
tenacity>=8.0.0
```

**Required Actions (see docs/Build-Process.md):**
- Generate `requirements.lock` with exact versions + hashes (`pip-compile --generate-hashes` or `pip freeze` + manual verification).
- Run `pip-audit` + `safety` + `bandit` on every build.
- Produce CycloneDX or SPDX SBOM.
- Consider replacing `recommenders` (Microsoft, older) and TensorFlow with lighter, auditable alternatives (e.g., PyTorch Geometric or pure JAX) for future variants.

---

## 6. RUNTIME SECURITY SETTINGS (FUTURE CONTAINER/KUBERNETES)

When containerized (Phase 1+ hardening):

```yaml
# Example Kubernetes Pod SecurityContext (baseline)
securityContext:
  runAsNonRoot: true
  runAsUser: 10001
  runAsGroup: 10001
  fsGroup: 10001
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]
  seccompProfile:
    type: RuntimeDefault
```

See NSA Kubernetes Hardening Guide and relevant container STIGs for additional controls (network policies, admission controllers, image signature verification).

---

## 7. CONFIGURATION CHANGE CONTROL

- All configuration changes to prompt templates, model parameters, or data loading logic **require** security review (see docs/Security-Hardening.md, CM-3).
- Changes must be accompanied by updated unit/integration tests and metric regression baselines.
- Signed commits (GPG) mandatory for any future protected branch.

---

## 8. VERIFICATION COMMANDS (RESEARCH)

```bash
# After any configuration or dependency change
python -m pip check
pip-audit -r requirements.txt
bandit -r src/
python -c "import os; print('OPENAI_API_KEY present:', bool(os.getenv('OPENAI_API_KEY')))"
```

---

*End of docs/Configuration.md*
