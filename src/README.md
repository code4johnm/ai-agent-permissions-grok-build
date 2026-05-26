# Source Code

Core implementation of the three experimental approaches: CF-only, IC-only, and IC+CF hybrid.

## Files

- `permission_cf_only.py` - Collaborative filtering baseline (LightGCN)
- `permission_ic_only.py` - In-context learning baseline
- `permission_ic_cf.py` - IC+CF hybrid (main contribution)
- `permission_assistant.py` - **NEW**: Runtime hybrid Permission Assistant demo (implements paper future work on usable interfaces, high-conf automation + defer, feedback/revocation, 4-option support)
- `evaluation_utils.py` - Shared evaluation utilities (now includes robust parsing + confidence threshold sweeps)

## Usage

Run scripts in order from the `src/` directory:

```bash
# 1. CF only - Generates CF scores (no API key required)
python permission_cf_only.py

# 2. IC only - Requires OpenAI API key
python permission_ic_only.py

# 3. IC+CF - Requires OpenAI API key + CF scores from step 1
python permission_ic_cf.py

# NEW: Interactive runtime assistant demo (paper future work - no key needed for mock mode)
python permission_assistant.py --demo
```

**Requirements:**
- IC-only and IC+CF require `OPENAI_API_KEY` in `.env` file
- All dependencies: `pip install -r ../requirements.txt`
- The assistant demo runs fully locally with strong mock predictor (real LLM optional)

## Key Improvements (Paper Gaps Implemented)

- Robust LLM JSON parsing (multi-strategy + optional Pydantic) — replaces fragile regex
- Confidence-thresholded evaluation + coverage reporting (reproduces paper 94.4% high-conf results)
- `permission_assistant.py`: first-class interactive hybrid system with auto high-conf decisions, defer-to-user (full 4 options), revocation, live feedback that affects future predictions, and audit logging. Directly addresses the "usable permission management", "human oversight for uncertain cases", and "enforcing predictions" directions in the paper Discussion/Conclusion.

## Outputs

All results automatically saved to `../results/`:
- `{method}_predictions.json` - Test predictions
- `{method}_metrics.json` - Performance metrics
- `cf_scores.csv` - CF scores (required by IC+CF)

See `../results/README.md` for details.
