# Build, Reproducibility, and Supply Chain Process

## AI Agent Permissions Research Prototype

**Version:** 1.0.0  
**Date:** 26 May 2026  
**Status:** Research Documentation

---

## 1. PURPOSE

This document defines the build process, reproducibility requirements, dependency management, and supply chain security controls for the AI Agent Permissions Research Prototype. Current practice is manual and research-oriented; this document also prescribes the hardened process required for any transition to accredited environments.

---

## 2. CURRENT BUILD PROCESS (RESEARCH)

**Build Type:** Pure Python source distribution. No compilation, no packaging into wheels or containers in the provided artifacts.

**Steps Performed by Researcher:**

```bash
# 1. Environment setup (one-time)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Secrets (never committed)
# Create .env with OPENAI_API_KEY (IC/Hybrid only)

# 3. Execute pipelines (order matters for hybrid)
cd src
python3 permission_cf_only.py          # Generates cf_scores.csv
python3 permission_ic_only.py
python3 permission_ic_cf.py

# 4. (Optional) Manual review of results/*.json and *.csv
```

**Reproducibility Limitations (Current):**
- No lockfile with hashes.
- TensorFlow + recommenders training is non-deterministic even with seeds in some paths.
- OpenAI model outputs are non-deterministic (temperature not explicitly 0 in current code; sampling behavior may vary).
- No container image or virtual environment export.
- Results directory is ephemeral and not versioned.

**Paper Results Reproducibility:** The published metrics in the IEEE S&P 2026 paper were generated under specific (undocumented in repo) random seeds, model versions, and prompt iterations. Exact numerical reproduction from this snapshot is **not guaranteed** without the original execution environment and API responses.

---

## 3. SECURE & REPRODUCIBLE BUILD REQUIREMENTS (FOR PRODUCTION / HIGH-SECURITY USE)

### 3.1 Dependency Management

**Current State:** Insecure (loose pins, no hashes, transitive risk from `recommenders` and `tensorflow`).

**Required Future State:**
1. Replace `requirements.txt` with two files:
   - `requirements.in` (human-maintained, loose upper bounds only)
   - `requirements.lock` (machine-generated, exact versions + hashes)
2. Use `pip-tools` or `uv`:
   ```bash
   pip-compile --generate-hashes requirements.in -o requirements.lock
   ```
3. On every build/CI:
   ```bash
   pip install --require-hashes -r requirements.lock
   pip-audit -r requirements.lock
   ```

### 3.2 Reproducible Execution Environment

**Phase 1 (Research Hardening):**
- Dockerfile (multi-stage) producing a minimal, signed image based on Chainguard Python or Iron Bank equivalent.
- `Dockerfile` must:
  - Use `COPY --from=...` for dependencies only
  - Run as non-root
  - Include SBOM generation step (`syft` or `cyclonedx-bom`)
  - Sign image with `cosign`

**Example Future Dockerfile Skeleton (Illustrative):**
```dockerfile
# syntax=docker/dockerfile:1.7
FROM cgr.dev/chainguard/python:3.12-dev AS builder
# ... install build deps, compile wheels ...

FROM cgr.dev/chainguard/python:3.12
COPY --from=builder /app/venv /app/venv
COPY src/ /app/src
USER 65532:65532
ENTRYPOINT ["python", "-m", "src.permission_runner"]
```

### 3.3 Build Attestation & Provenance (SLSA / SSDF)

**Required for Accredited Path:**
- GitHub Actions or GitLab CI pipeline enforcing:
  - Signed commits on protected branches
  - `cosign sign` of container images + SBOM
  - SLSA provenance generation (`slsa-github-generator`)
  - Trivy/Grype scan with failure on HIGH/CRITICAL
- All build artifacts carry:
  - SPDX or CycloneDX SBOM (attached or referenced via tag)
  - Cosign signature + Rekor transparency log entry (when using public Rekor)

### 3.4 Reproducibility for ML Components

- Record exact `OPENAI_MODEL`, prompt template hash, and `cf_scores.csv` git SHA (or content hash) with every prediction run.
- For CF: Save full model checkpoint + hparams + random seed used.
- Consider deterministic LLM inference (where supported) or record full response including `system_fingerprint` from OpenAI.

---

## 4. CONTINUOUS INTEGRATION / QUALITY GATES (FUTURE)

**Minimum Gates Before Merge (when CI is stood up):**
1. `pip-audit` + `safety` clean (no known CVEs in dependencies)
2. `bandit -r src/ -ll` (no HIGH severity issues)
3. `semgrep --config=auto src/` (or custom LLM injection rules)
4. Python syntax + import validation on all three pipelines
5. Metric regression test (if baseline metrics committed): fail if F1 drops > threshold vs. paper-reported hybrid
6. SBOM generation + diff against previous (alert on new high-risk components)

**No CI exists in the current workspace.** Creation of `.github/workflows/` or equivalent is a Phase 1 hardening deliverable.

---

## 5. ARTIFACT MANAGEMENT

**Never Commit:**
- `.env*`
- `results/` (except its README)
- Any file containing real API responses or participant-level raw predictions that could enable re-identification

**Recommended .gitignore Additions (verify):**
```
.env
.env.*
results/*.json
results/*.csv
lightgcn_model/
lightgcn_summaries/
__pycache__/
*.pyc
.venv/
venv/
```

---

## 6. BUILD VERIFICATION CHECKLIST (RESEARCH USE)

- [ ] `pip-audit` reports zero HIGH/CRITICAL
- [ ] All Python files parse cleanly (`python -m py_compile src/*.py`)
- [ ] CF pipeline completes without GPU and produces `cf_scores.csv`
- [ ] IC-only pipeline completes (with valid key) and produces metrics
- [ ] Hybrid pipeline runs after CF and produces metrics
- [ ] No new files created outside `results/`
- [ ] No secrets appear in git diff (`git diff --cached | grep -i key`)

---

## 7. TRANSITION MILESTONES

| Phase | Build Capability | Supply Chain Controls |
|-------|------------------|-----------------------|
| Current (Research) | Manual venv + pip | None |
| Phase 1 (Hardened Research) | Reproducible container + SBOM | Hashed lockfile, image signing |
| Phase 2 (Pre-Accred) | CI-gated, attested builds | SLSA L2+, vulnerability management program |
| Phase 3 (Accredited) | Air-gapped reproducible build | Full SSDLC + signed artifacts + on-prem model registry |

---

*End of docs/Build-Process.md*
