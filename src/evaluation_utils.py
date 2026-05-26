#!/usr/bin/env python3
"""
Shared evaluation utilities for all permission prediction methods.

Provides unified metrics calculation and output formatting across:
- CF-only (Collaborative Filtering)
- IC-only (In-Context Learning)
- IC+CF (Hybrid approach)
"""

# Target: Linux platforms (PEP 8 compliant, UTF-8, forward-slash paths)

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

logger = logging.getLogger(__name__)

try:
    from pydantic import BaseModel, ValidationError, ConfigDict
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    BaseModel = object  # type: ignore
    ValidationError = Exception  # type: ignore


def calculate_metrics(y_true, y_pred, method_name, threshold=None):
    """
    Calculate standard evaluation metrics.

    Args:
        y_true: List of true labels (0 or 1)
        y_pred: List of predicted labels (0 or 1)
        method_name: Name of the method (e.g., "IC Only", "IC+CF", "CF Only")
        threshold: Optional threshold used for binary classification

    Returns:
        dict: Dictionary containing all metrics
    """
    # Calculate metrics
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    # Calculate FPR and FNR from confusion matrix
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0

    metrics = {
        "method": method_name,
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "fpr": float(fpr),
        "fnr": float(fnr),
        "n_predictions": len(y_true)
    }

    if threshold is not None:
        metrics["threshold"] = float(threshold)

    return metrics


def save_metrics(metrics, output_path):
    """Save metrics to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"✓ Metrics saved to {output_path}")


def save_predictions(predictions, output_path):
    """Save predictions to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(predictions, f, indent=2)
    print(f"✓ Predictions saved to {output_path}")


def save_results_csv(results_df, output_path):
    """Save detailed results to CSV file."""
    results_df.to_csv(output_path, index=False)
    print(f"✓ Detailed results saved to {output_path}")


def print_metrics(metrics):
    """Print metrics in a formatted table."""
    print(f"\n{'='*60}")
    print(f"{metrics['method']} - Evaluation Metrics")
    print(f"{'='*60}")
    print(f"Predictions:  {metrics['n_predictions']:,}")
    if 'n_participants' in metrics:
        print(f"Participants: {metrics['n_participants']}")
    if 'threshold' in metrics:
        print(f"Threshold:    {metrics['threshold']:.4f}")
    print(f"\nPerformance:")
    print(f"  Accuracy:   {metrics['accuracy']*100:6.1f}%")
    print(f"  Precision:  {metrics['precision']*100:6.1f}%")
    print(f"  Recall:     {metrics['recall']*100:6.1f}%")
    print(f"  F1 Score:   {metrics['f1']*100:6.1f}%")
    print(f"  FPR:        {metrics['fpr']*100:6.1f}%")
    print(f"  FNR:        {metrics['fnr']*100:6.1f}%")
    print(f"{'='*60}\n")


def evaluate_predictions_from_file(predictions_file, method_name):
    """
    Evaluate predictions from JSON file (IC-only or IC+CF format).

    Args:
        predictions_file: Path to predictions JSON file
        method_name: Name of the method

    Returns:
        dict: Metrics dictionary
    """
    with open(predictions_file, 'r') as f:
        results = json.load(f)

    all_true = []
    all_pred = []
    n_participants = 0

    for participant_id, data in results.items():
        if data.get('skipped') or 'error' in data:
            continue

        n_participants += 1
        predictions = data.get('predictions', [])
        ground_truth = data.get('ground_truth', [])

        # Match predictions with ground truth by query ID
        for gt_item in ground_truth:
            query_id = gt_item['id']
            gt_permissions = gt_item.get('answer', {})

            # Find corresponding prediction
            pred_item = next((p for p in predictions if p.get('id') == query_id), None)
            pred_permissions = pred_item.get('permission', {}) if pred_item else {}

            # For each data type in ground truth
            for data_type, gt_label in gt_permissions.items():
                # If no prediction for this data type, default to "No, never share" (0)
                if data_type in pred_permissions:
                    pred_label = pred_permissions[data_type].get('label', '')
                    pred_binary = 1 if "Yes" in pred_label else 0
                else:
                    pred_binary = 0  # Default: No, never share

                # Convert ground truth to binary
                gt_binary = 1 if "Yes" in gt_label else 0

                all_true.append(gt_binary)
                all_pred.append(pred_binary)

    if len(all_true) == 0:
        raise ValueError(f"No valid predictions found in {predictions_file}")

    metrics = calculate_metrics(all_true, all_pred, method_name, threshold=0.5)
    metrics['n_participants'] = n_participants

    return metrics


# =============================================================================
# Robust LLM Output Parsing (addresses paper "Model Robustness" gap + fragility noted in Architecture.md)
# =============================================================================

class PermissionItem(BaseModel):
    """Single data-type permission prediction with label and optional confidence."""
    model_config = ConfigDict(extra='ignore') if PYDANTIC_AVAILABLE else {}
    label: str
    score: Optional[float] = 0.5


class PermissionPrediction(BaseModel):
    """One query's permission block."""
    model_config = ConfigDict(extra='ignore') if PYDANTIC_AVAILABLE else {}
    query: Optional[str] = None
    id: Optional[int] = None
    permission: Dict[str, PermissionItem] = {}


class LLMResponse(BaseModel):
    """Top-level expected LLM response for permission predictions."""
    model_config = ConfigDict(extra='ignore') if PYDANTIC_AVAILABLE else {}
    # Pydantic v1 __root__ fallback (v2 RootModel preferred when available)
    __root__: List[PermissionPrediction] = (
        [] if not PYDANTIC_AVAILABLE else None
    )  # type: ignore


def _clean_llm_json(text: str) -> str:
    """Strip markdown fences, leading/trailing noise, and common LLM JSON artifacts."""
    if not text:
        return ""
    t = text.strip()
    # Remove ```json ... ``` or ``` ... ```
    t = re.sub(r'^```(?:json)?\s*', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*```$', '', t)
    # Remove any leading explanatory text before first [ or {
    first_bracket = min(
        (t.find("["), t.find("{")),
        key=lambda x: x if x >= 0 else 999999,
    )
    if first_bracket > 0 and first_bracket < 200:  # heuristic: not too far
        t = t[first_bracket:]
    # Trim trailing junk after last ] or }
    last_bracket = max(t.rfind(']'), t.rfind('}'))
    if last_bracket > 0:
        t = t[:last_bracket+1]
    return t.strip()


def robust_extract_predictions(response: str) -> List[Dict[str, Any]]:
    """
    Much more robust extraction than the original re.search(r'\\[.*\\]') .

    Tries (in order):
    1. Direct json.loads (after cleaning)
    2. Regex for outermost JSON array
    3. Pydantic validation (if available) for schema enforcement
    4. Fallbacks + logging

    Returns list of prediction dicts (or [] on total failure).
    """
    if not response or not isinstance(response, str):
        return []

    cleaned = _clean_llm_json(response)

    # Attempt 1: direct
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            # sometimes LLM returns {"permissions": [...] } wrapper
            for key in ("permissions", "predictions", "results", "output"):
                if key in parsed and isinstance(parsed[key], list):
                    return parsed[key]
            return [parsed]  # single object case
    except json.JSONDecodeError:
        pass

    # Attempt 2: regex for array (improved, handles nested better than original)
    try:
        # Find the first complete top-level JSON array
        array_match = re.search(r'(\[[\s\S]*\])', cleaned, re.DOTALL)
        if array_match:
            candidate = array_match.group(1)
            # Balance check heuristic
            if candidate.count('[') == candidate.count(']'):
                parsed = json.loads(candidate)
                if isinstance(parsed, list):
                    return parsed
    except (json.JSONDecodeError, Exception):
        pass

    # Attempt 3: Pydantic strict validation (best for robustness)
    if PYDANTIC_AVAILABLE:
        try:
            # Try as list of predictions
            model = LLMResponse.model_validate_json(cleaned)  # type: ignore[attr-defined]
            # pydantic v2 root model handling
            if hasattr(model, 'root'):
                items = model.root  # type: ignore
            else:
                items = model.__root__ if hasattr(model, '__root__') else []
            if items:
                return [
                    item.model_dump() if hasattr(item, "model_dump") else item
                    for item in items
                ]
            return []
        except ValidationError:
            pass
        except Exception:
            pass

    # Last resort: try to parse any JSON objects we can find
    try:
        objs = re.findall(r'\{[^{}]*"label"[^{}]*\}', cleaned)
        if objs:
            return [json.loads(o) for o in objs if '"label"' in o]
    except Exception:
        pass

    logger = logging.getLogger(__name__) if 'logging' in globals() else None
    if logger:
        logger.warning("robust_extract_predictions: all strategies failed. Response head: %s", cleaned[:300])
    return []


# Backwards-compatible alias for existing call sites
def extract_predictions(response: str) -> List[Dict[str, Any]]:
    """Legacy wrapper; prefer robust_extract_predictions in new code."""
    return robust_extract_predictions(response)


def extract_decisions_with_scores(
    predictions_file: str
) -> List[Tuple[int, int, float]]:
    """
    Extract all (gt_binary, pred_binary, confidence_score) triples from an IC/Hybrid
    predictions file that stores per-datatype 'label' and 'score'.

    Returns list of tuples for threshold analysis. Skips entries without valid scores.
    """
    with open(predictions_file, 'r') as f:
        results = json.load(f)

    decisions: List[Tuple[int, int, float]] = []

    for participant_id, data in results.items():
        if data.get('skipped') or 'error' in data:
            continue

        predictions = data.get('predictions', [])
        ground_truth = data.get('ground_truth', [])

        for gt_item in ground_truth:
            query_id = gt_item['id']
            gt_permissions = gt_item.get('answer', {})

            pred_item = next((p for p in predictions if p.get('id') == query_id), None)
            pred_permissions = pred_item.get('permission', {}) if pred_item else {}

            for data_type, gt_label in gt_permissions.items():
                gt_binary = 1 if "Yes" in gt_label else 0

                if data_type in pred_permissions:
                    p = pred_permissions[data_type]
                    pred_label = p.get('label', '')
                    pred_binary = 1 if "Yes" in pred_label else 0
                    # score may be missing or string; coerce
                    raw_score = p.get('score', 0.5)
                    try:
                        conf = float(raw_score)
                    except (ValueError, TypeError):
                        conf = 0.5
                else:
                    pred_binary = 0
                    conf = 0.0  # no prediction -> treat as low conf deny

                decisions.append((gt_binary, pred_binary, conf))

    return decisions


def evaluate_at_threshold(
    decisions: List[Tuple[int, int, float]],
    threshold: float,
    method_name: str
) -> Dict[str, Any]:
    """
    Compute binary classification metrics using only decisions where conf >= threshold.
    Returns metrics dict + 'coverage' (fraction of decisions above threshold) + 'n_used'.
    """
    filtered_true = []
    filtered_pred = []
    total = len(decisions)

    for gt, pred, conf in decisions:
        if conf >= threshold:
            filtered_true.append(gt)
            filtered_pred.append(pred)

    n_used = len(filtered_true)
    coverage = n_used / total if total > 0 else 0.0

    if n_used == 0:
        metrics = {
            "method": f"{method_name} (thresh={threshold:.2f})",
            "accuracy": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "fpr": 0.0,
            "fnr": 0.0,
            "n_predictions": 0,
            "coverage": coverage,
            "n_used": 0,
            "n_total": total,
            "threshold": threshold,
        }
        return metrics

    m = calculate_metrics(filtered_true, filtered_pred, f"{method_name} @ {threshold:.2f}", threshold=threshold)
    m["coverage"] = float(coverage)
    m["n_used"] = n_used
    m["n_total"] = total
    m["threshold"] = float(threshold)
    return m


def evaluate_with_confidence_thresholds(
    predictions_file: str,
    method_name: str,
    confidence_thresholds: Optional[List[float]] = None
) -> Dict[str, Any]:
    """
    Full analysis: full-coverage metrics + metrics at multiple confidence thresholds.
    This reproduces the high-confidence / reduced-coverage analysis from the paper
    (e.g., 94.4% accuracy at ~0.91 threshold with ~26% coverage for hybrid).

    Returns:
        {
          "full_coverage": <standard metrics>,
          "thresholded": [ list of per-threshold metric dicts ],
          "best_high_conf": <the threshold result with highest acc among those with coverage> or similar
        }
    """
    if confidence_thresholds is None:
        confidence_thresholds = [0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.91, 0.95]

    decisions = extract_decisions_with_scores(predictions_file)

    full_metrics = evaluate_predictions_from_file(predictions_file, method_name)
    # Rename for clarity
    full_metrics = {**full_metrics, "coverage": 1.0, "n_used": full_metrics.get("n_predictions", 0)}

    thresholded_results = []
    for t in confidence_thresholds:
        m = evaluate_at_threshold(decisions, t, method_name)
        thresholded_results.append(m)

    # Pick "best" high-conf: highest accuracy among those with coverage >= 0.2 (arbitrary, paper used ~0.26)
    valid_high = [r for r in thresholded_results if r.get("coverage", 0) >= 0.15 and r.get("n_used", 0) > 10]
    best_high = max(valid_high, key=lambda x: x.get("accuracy", 0)) if valid_high else None

    return {
        "full_coverage": full_metrics,
        "thresholded": thresholded_results,
        "recommended_high_conf": best_high,
        "method": method_name,
    }


def print_threshold_analysis(analysis: Dict[str, Any]):
    """Pretty-print the confidence threshold sweep results."""
    print(f"\n{'='*70}")
    print(f"CONFIDENCE THRESHOLD ANALYSIS: {analysis.get('method', 'Unknown')}")
    print(f"{'='*70}")
    full = analysis["full_coverage"]
    print(f"Full coverage (all decisions, effective thresh ~0.5):")
    print(f"  Accuracy: {full['accuracy']*100:5.1f}%  |  n={full['n_predictions']}")
    print(f"\nPer-threshold high-confidence subsets (paper-style analysis):")
    print(f"{'Thresh':>8} {'Acc':>8} {'Prec':>8} {'Rec':>8} {'Cov':>8} {'N used':>8}")
    print("-" * 60)
    for r in analysis["thresholded"]:
        print(f"{r['threshold']:8.2f} {r['accuracy']*100:7.1f}% {r['precision']*100:7.1f}% "
              f"{r['recall']*100:7.1f}% {r.get('coverage',0)*100:7.1f}% {r.get('n_used',0):>8}")
    if analysis.get("recommended_high_conf"):
        bh = analysis["recommended_high_conf"]
        print(f"\nRecommended operating point (high-conf, good coverage): "
              f"thresh={bh['threshold']:.2f}  acc={bh['accuracy']*100:.1f}%  coverage={bh['coverage']*100:.1f}%")
    print(f"{'='*70}\n")
