# Troubleshooting Guide

## AI Agent Permissions Research Prototype

**Version:** 1.0.0  
**Date:** 26 May 2026  
**Status:** Research Documentation

---

## 1. PURPOSE

This document provides diagnostic procedures, common failure modes, and resolution steps for the research prototype. It is intended for research personnel and future system administrators of hardened variants.

---

## 2. COMMON ISSUES AND RESOLUTIONS

### 2.1 Environment and Dependency Errors

**Symptom:** `ModuleNotFoundError: No module named 'recommenders'` or `tensorflow`

**Cause:** Incomplete or conflicting Python environment.

**Resolution:**
```bash
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip check
```

**Symptom:** TensorFlow GPU warnings or CUDA errors (even on CPU-only systems)

**Cause:** TensorFlow detects GPU libraries but no compatible device.

**Resolution (Research Only):**
```bash
export TF_CPP_MIN_LOG_LEVEL=3
# Or install CPU-only variant if GPU not required:
pip install tensorflow-cpu
```

### 2.2 OpenAI / LLM Pipeline Failures

**Symptom:** `EnvironmentError: OpenAI API key not found`

**Resolution:**
- Verify `.env` exists in project root (sibling of `src/`)
- Confirm `load_dotenv()` executes before any OpenAI client creation
- Check variable name exactly: `OPENAI_API_KEY`
- Export manually for testing: `export OPENAI_API_KEY=sk-...`

**Symptom:** `RateLimitError` or repeated 429s despite tenacity retries

**Cause:** Account rate limits or high concurrency (MAX_WORKERS=5).

**Resolution:**
- Reduce `MAX_WORKERS` to 2 or 1 in `permission_ic_only.py` and `permission_ic_cf.py`
- Add longer `wait_exponential` multipliers
- Request higher tier from OpenAI or switch to approved gateway with queuing

**Symptom:** `json.JSONDecodeError` or empty predictions for many participants

**Cause:** LLM response did not contain valid JSON array (common with newer reasoning models or long contexts).

**Current Workaround:** The `extract_predictions()` regex fallback sometimes succeeds. For persistent failures:
- Inspect raw response in logs (add `print(response)` temporarily)
- Shorten prompt (reduce training examples or top-K)
- Switch to model variant with stronger JSON mode support (when available)

**Security Note:** Never log raw LLM responses containing participant data in production logs.

### 2.3 CF Pipeline Failures

**Symptom:** `KeyError` during LightGCN training or scoring (user/item not in mapping)

**Cause:** Mismatch between filtered participant set and interaction data, or query ID changes.

**Resolution:**
- Re-run from clean `results/` (delete `cf_scores.csv`)
- Verify `processed_dataset.json` and `user_study.json` are unmodified from repository
- Confirm 181 participants are present after filtering

**Symptom:** Extremely long training time or OOM on modest hardware

**Resolution:**
- Reduce `EPOCHS` to 30–50 for experimentation (note: metrics will differ from paper)
- Lower `BATCH_SIZE`
- Run on CPU-only (slower but stable)
- The paper used 120 epochs; this is the dominant compute step

### 2.4 Hybrid Pipeline Specific

**Symptom:** `FileNotFoundError: ../results/cf_scores.csv`

**Resolution:** Execute `permission_cf_only.py` to completion **before** running `permission_ic_cf.py`.

**Symptom:** Hybrid metrics identical or worse than IC-only

**Possible Causes:**
- CF scores not yet generated or stale
- `TOP_K` recommendations not surfacing useful signals for the test split
- LLM ignoring the additional context (prompt engineering issue)

**Debug:** Add logging of `cf_recommendations` string length and sample content per participant.

### 2.5 Data and Path Issues

**Symptom:** Scripts fail with paths like `../data/...` when run from wrong directory

**Rule:** All three permission scripts **must** be executed with `cwd` inside `src/`.

```bash
cd src
python permission_*.py   # Correct
python ../src/permission_*.py  # Often breaks relative paths
```

**Symptom:** `processed_dataset.json` missing "testing" or "training" keys for some participants

**Expected:** Some participants are skipped (logged). This is by design in the paper methodology.

---

## 3. DIAGNOSTIC COMMANDS

```bash
# Environment sanity
python --version
pip list | grep -E 'openai|tensorflow|recommenders|pandas|scikit'
python -c "import os; print('.env present:', os.path.exists('../.env'))"

# Data integrity (from src/)
python -c "
import json
with open('../data/processed_dataset.json') as f:
    ds = json.load(f)
print('Participants:', len(ds))
print('Sample keys for first P:', list(next(iter(ds.values())).keys()))
"

# Quick metric sanity after run
python -c "
import json
with open('../results/ic_cf_metrics.json') as f:
    m = json.load(f)
print(m)
"
```

---

## 4. LOGGING AND DEBUGGING

- IC and hybrid scripts use `logging` at INFO level.
- Increase verbosity: edit `logging.basicConfig(level=logging.DEBUG)`
- For LLM prompt debugging (research only, privacy risk): temporarily print the full prompt before `llm_inference()`.
- **Never** enable DEBUG logging or prompt printing when processing real (even anonymized) participant data on shared systems.

---

## 5. RESULTS VALIDATION

After a successful run, verify:
- All three `*_metrics.json` files exist with `n_predictions > 0`
- `cf_scores.csv` has >10k rows (rough sanity for 181 users)
- Metrics files contain "f1", "accuracy", "fpr", "fnr" keys
- No "error" entries dominate `*_predictions.json`

---

## 6. ESCALATION

Persistent failures after following this guide:
1. Capture sanitized logs (no API keys, no raw participant bios)
2. Note exact Python / library versions + OS
3. Open issue in project tracker (for future engineering phase) or contact original research team for academic questions
4. For security-related anomalies (unexpected data leakage, model behavior suggesting poisoning), follow [SECURITY.md](SECURITY.md) reporting procedures immediately.

---

*End of docs/Troubleshooting.md*
