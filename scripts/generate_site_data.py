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
    for row in rows:
        n = parse_int(row.get("n")) or 0
        exact = parse_int(row.get("exact")) or 0
        minor = parse_int(row.get("minor")) or 0
        hard = parse_int(row.get("hard")) or 0
        hard_miss = parse_int(row.get("hard_miss")) or 0
        hard_over = parse_int(row.get("hard_over")) or 0
        n_errors = parse_int(row.get("n_errors")) or 0

        model = {
            "rank": parse_int(row.get("rank")),
            "model": row["model"],
            "tier": row["tier"],
            "cw_pct": parse_float(row.get("cw_pct")),
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
            "exact_rate": pct(exact, n),
            "minor_rate": pct(minor, n),
            "hard_rate": pct(hard, n),
            "critical_miss_rate": pct(hard_miss, n),
            "false_review_load": pct(hard_over, n),
            "llm_error_rate": pct(n_errors, n),
        }
        models.append(model)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "leaderboard": str(LEADERBOARD_PATH.relative_to(REPO_ROOT)),
        },
        "summary": {
            "model_count": len(models),
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
                "key": "ord_pct",
                "label": "Ordinal %",
                "direction": "higher",
                "format": "percent",
                "description": "Distance-based score without confidence weighting.",
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
                "key": "critical_miss_rate",
                "label": "Critical Miss Rate %",
                "direction": "lower",
                "format": "percent",
                "description": "Share of findings where a real threat was dismissed as benign.",
            },
            {
                "key": "false_review_load",
                "label": "False Review Load %",
                "direction": "lower",
                "format": "percent",
                "description": "Share of findings where benign activity was escalated as malicious.",
            },
            {
                "key": "hard_rate",
                "label": "Hard Error Rate %",
                "direction": "lower",
                "format": "percent",
                "description": "Combined rate of TP↔FP hard classification errors.",
            },
            {
                "key": "minor_rate",
                "label": "Minor Miss Rate %",
                "direction": "lower",
                "format": "percent",
                "description": "Share of findings where the model was one classification step away.",
            },
            {
                "key": "exact_rate",
                "label": "Exact Match Rate %",
                "direction": "higher",
                "format": "percent",
                "description": "Share of findings classified exactly like the ground truth.",
            },
            {
                "key": "llm_error_rate",
                "label": "LLM Error Rate %",
                "direction": "lower",
                "format": "percent",
                "description": "Share of findings without a usable model response.",
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
                "x": "false_review_load",
                "y": "critical_miss_rate",
                "x_scale": "linear",
            },
            {
                "key": "cw-vs-ord",
                "label": "CW % vs Ordinal %",
                "x": "ord_pct",
                "y": "cw_pct",
                "x_scale": "linear",
            },
            {
                "key": "cw-vs-mae",
                "label": "CW % vs MAE",
                "x": "mae",
                "y": "cw_pct",
                "x_scale": "linear",
            },
            {
                "key": "cw-vs-speed",
                "label": "CW % vs Speed",
                "x": "avg_seconds_per_event",
                "y": "cw_pct",
                "x_scale": "log",
            },
        ],
        "models": models,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
