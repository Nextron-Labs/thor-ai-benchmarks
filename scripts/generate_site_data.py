#!/usr/bin/env python3
"""Generate the static data bundle used by the interactive benchmark explorer."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
LEADERBOARD_PATH = REPO_ROOT / "combined" / "leaderboard.json"
OUTPUT_PATH = REPO_ROOT / "docs" / "data" / "leaderboard-explorer.json"


def parse_float(value):
    if value in (None, "", "-", "–"):
        return None
    return float(value)


def parse_int(value):
    if value in (None, "", "-", "–"):
        return None
    return int(value)


def parse_rank(value):
    if value in (None, "", "-", "–"):
        return None, None
    text = str(value)
    try:
        numeric = int(text)
    except ValueError:
        return text, None
    return text, numeric


def parse_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).lower() == "true"


def pct(part, total):
    if not total:
        return None
    return round((part / total) * 100, 2)


def main():
    rows = json.loads(LEADERBOARD_PATH.read_text())

    models = []
    for index, row in enumerate(rows):
        n = parse_int(row.get("n")) or 0
        exact = parse_int(row.get("exact")) or 0
        minor = parse_int(row.get("minor")) or 0
        hard = parse_int(row.get("hard")) or 0
        hard_miss = parse_int(row.get("hard_miss")) or 0
        hard_over = parse_int(row.get("hard_over")) or 0
        n_errors = parse_int(row.get("n_errors")) or 0
        rank_label, rank_numeric = parse_rank(row.get("rank"))

        model = {
            "rank_label": rank_label,
            "rank_numeric": rank_numeric,
            "rank_sort": rank_numeric if rank_numeric is not None else 1000 + index,
            "model": row["model"],
            "tier": row["tier"],
            "cw_pct": parse_float(row.get("cw_pct")),
            "ots_pct": parse_float(row.get("ots_pct")),
            "ots_macro": parse_float(row.get("ots_macro")),
            "balanced_ots": parse_float(row.get("balanced_ots")),
            "threat_capture": parse_float(row.get("threat_capture")),
            "critical_miss": parse_float(row.get("critical_miss")),
            "anomaly_capture": parse_float(row.get("anomaly_capture")),
            "anomaly_suppression": parse_float(row.get("anomaly_suppression")),
            "false_review": parse_float(row.get("false_review")),
            "false_escalation": parse_float(row.get("false_escalation")),
            "ord_pct": parse_float(row.get("ord_pct")),
            "mae": parse_float(row.get("mae")),
            "rmse": parse_float(row.get("rmse")),
            "avg_seconds_per_event": parse_float(row.get("avg_seconds_per_event")),
            "total_tokens": parse_int(row.get("total_tokens")),
            "exact": exact,
            "minor": minor,
            "hard": hard,
            "hard_miss": hard_miss,
            "hard_over": hard_over,
            "n_errors": n_errors,
            "n": n,
            "incomplete": parse_bool(row.get("incomplete")),
            "is_baseline": row["tier"] == "baseline",
            "exact_rate_all_findings": pct(exact, n),
            "minor_rate_all_findings": pct(minor, n),
            "hard_rate_all_findings": pct(hard, n),
            "hard_miss_share_all_findings": pct(hard_miss, n),
            "hard_over_share_all_findings": pct(hard_over, n),
            "llm_error_rate_all_findings": pct(n_errors, n),
        }
        models.append(model)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "leaderboard": str(LEADERBOARD_PATH.relative_to(REPO_ROOT)),
        },
        "summary": {
            "model_count": len(models),
            "baseline_count": sum(1 for row in models if row["is_baseline"]),
            "benchmarked_model_count": sum(1 for row in models if not row["is_baseline"]),
            "complete_count": sum(1 for row in models if not row["incomplete"]),
            "incomplete_count": sum(1 for row in models if row["incomplete"]),
        },
        "metrics": [
            {
                "key": "cw_pct",
                "label": "CW %",
                "direction": "higher",
                "format": "percent",
                "description": "Confidence-weighted benchmark score.",
            },
            {
                "key": "balanced_ots",
                "label": "Balanced OTS",
                "direction": "higher",
                "format": "percent",
                "description": "Operational triage score balanced across FP, Inc, and TP classes.",
            },
            {
                "key": "critical_miss",
                "label": "Critical Miss Rate %",
                "direction": "lower",
                "format": "percent",
                "description": "Share of true positives classified as false positive.",
            },
            {
                "key": "false_review",
                "label": "False Review Load %",
                "direction": "lower",
                "format": "percent",
                "description": "Share of false positives still sent to review as Inc or TP.",
            },
            {
                "key": "threat_capture",
                "label": "Threat Capture Rate %",
                "direction": "higher",
                "format": "percent",
                "description": "Share of true positives still sent to review as Inc or TP.",
            },
            {
                "key": "false_escalation",
                "label": "False Escalation Rate %",
                "direction": "lower",
                "format": "percent",
                "description": "Share of false positives escalated all the way to TP.",
            },
            {
                "key": "ord_pct",
                "label": "Ordinal %",
                "direction": "higher",
                "format": "percent",
                "description": "Distance-based score without confidence weighting.",
            },
            {
                "key": "ots_pct",
                "label": "OTS %",
                "direction": "higher",
                "format": "percent",
                "description": "Operational triage score across the full benchmark set.",
            },
            {
                "key": "ots_macro",
                "label": "OTS Macro",
                "direction": "higher",
                "format": "percent",
                "description": "Operational triage score macro-averaged across classes.",
            },
            {
                "key": "anomaly_capture",
                "label": "Anomaly Capture %",
                "direction": "higher",
                "format": "percent",
                "description": "Share of inconclusive or suspicious findings still surfaced for review.",
            },
            {
                "key": "anomaly_suppression",
                "label": "Anomaly Suppression %",
                "direction": "lower",
                "format": "percent",
                "description": "Share of anomaly-like findings suppressed out of review.",
            },
            {
                "key": "mae",
                "label": "MAE",
                "direction": "lower",
                "format": "decimal",
                "description": "Priority-score mean absolute error.",
            },
            {
                "key": "rmse",
                "label": "RMSE",
                "direction": "lower",
                "format": "decimal",
                "description": "Priority-score root mean squared error.",
            },
            {
                "key": "avg_seconds_per_event",
                "label": "Seconds / Event",
                "direction": "lower",
                "format": "seconds",
                "description": "Average wall-clock latency per finding reviewed.",
            },
            {
                "key": "exact_rate_all_findings",
                "label": "Exact Match Rate %",
                "direction": "higher",
                "format": "percent",
                "description": "Share of all findings classified exactly like the ground truth.",
            },
            {
                "key": "minor_rate_all_findings",
                "label": "Minor Miss Rate %",
                "direction": "lower",
                "format": "percent",
                "description": "Share of all findings where the model was one classification step away.",
            },
            {
                "key": "hard_rate_all_findings",
                "label": "Hard Error Rate %",
                "direction": "lower",
                "format": "percent",
                "description": "Combined TP↔FP hard error share across all findings.",
            },
            {
                "key": "llm_error_rate_all_findings",
                "label": "LLM Error Rate %",
                "direction": "lower",
                "format": "percent",
                "description": "Share of all findings without a usable model response.",
            },
            {
                "key": "total_tokens",
                "label": "Total Tokens",
                "direction": "lower",
                "format": "integer",
                "description": "Total tokens consumed across the benchmark run.",
            },
        ],
        "presets": [
            {
                "key": "miss-vs-review",
                "label": "Critical Miss Rate vs False Review Load",
                "x": "false_review",
                "y": "critical_miss",
                "x_scale": "linear",
            },
            {
                "key": "balanced-ots-vs-review",
                "label": "Balanced OTS vs False Review Load",
                "x": "false_review",
                "y": "balanced_ots",
                "x_scale": "linear",
            },
            {
                "key": "cw-vs-balanced-ots",
                "label": "CW % vs Balanced OTS",
                "x": "cw_pct",
                "y": "balanced_ots",
                "x_scale": "linear",
            },
            {
                "key": "cw-vs-speed",
                "label": "CW % vs Speed",
                "x": "avg_seconds_per_event",
                "y": "cw_pct",
                "x_scale": "log",
            },
            {
                "key": "cw-vs-mae",
                "label": "CW % vs MAE",
                "x": "mae",
                "y": "cw_pct",
                "x_scale": "linear",
            },
        ],
        "models": models,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
