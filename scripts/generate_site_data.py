#!/usr/bin/env python3
"""Generate the static data bundle used by the interactive benchmark explorer."""

from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from openrouter_costs import estimate_run_cost_cents, load_pricing_snapshot

REPO_ROOT = Path(__file__).resolve().parent.parent
LEADERBOARD_PATH = REPO_ROOT / "combined" / "leaderboard.json"
OUTPUT_PATH = REPO_ROOT / "docs" / "data" / "leaderboard-explorer.json"
DOCS_CHARTS_DIR = REPO_ROOT / "docs" / "charts"
OPERATIONAL_SUMMARY_BY_TIER_PATH = REPO_ROOT / "combined" / "operational-profile-summary-by-tier.csv"

PROFILE_META = {
    "high_safety": {
        "label": "High-safety",
        "use_case": "High-safety triage",
        "file": REPO_ROOT / "combined" / "operational-profile-high-safety.csv",
    },
    "balanced_soc": {
        "label": "Balanced SOC",
        "use_case": "Balanced SOC triage",
        "file": REPO_ROOT / "combined" / "operational-profile-balanced-soc.csv",
    },
    "noise_reduction": {
        "label": "Noise-reduction",
        "use_case": "Noise reduction / high-volume triage",
        "file": REPO_ROOT / "combined" / "operational-profile-noise-reduction.csv",
    },
}

PROFILE_ORDER = ["high_safety", "balanced_soc", "noise_reduction"]

TIER_LABELS = {
    "closed_source": "Closed Source / Vendor API",
    "open_source_pro": "Open Source / Pro Hardware",
    "open_source_consumer": "Open Source / Consumer Hardware",
}

TIER_KEY_BY_SUMMARY_LABEL = {
    "Closed Source (Vendor API)": "closed_source",
    "Open Source (Pro Hardware)": "open_source_pro",
    "Open Source (Consumer Hardware)": "open_source_consumer",
}

CHART_GALLERY = [
    {
        "key": "operational-profile-summary",
        "title": "Operational Profile Summary",
        "filename": "operational-profile-summary.png",
        "description": "Compares the current profile leaders against the always-inc baseline across the main operational metrics.",
    },
    {
        "key": "operational-profile-summary-by-tier",
        "title": "Operational Profile Summary by Tier",
        "filename": "operational-profile-summary-by-tier.png",
        "description": "Shows the current recommended profile leader inside each deployment tier.",
    },
    {
        "key": "classification-breakdown",
        "title": "Classification Breakdown",
        "filename": "classification-breakdown.png",
        "description": "Shows how each model's classifications split into exact matches, near misses, and hard errors.",
    },
    {
        "key": "quality-vs-speed",
        "title": "Quality vs Speed",
        "filename": "quality-vs-speed.png",
        "description": "Plots confidence-weighted quality against average seconds per event.",
    },
    {
        "key": "quality-vs-cost",
        "title": "Quality vs Cost",
        "filename": "quality-vs-cost.png",
        "description": "Plots confidence-weighted quality against estimated benchmark run cost.",
    },
    {
        "key": "cw-leaderboard",
        "title": "CW Leaderboard",
        "filename": "cw-leaderboard.png",
        "description": "Ranks models by the classic confidence-weighted benchmark score.",
    },
    {
        "key": "operational-error-breakdown",
        "title": "Operational Error Breakdown",
        "filename": "operational-error-breakdown.png",
        "description": "Breaks operationally relevant error types into critical misses, false review, and escalation-related trade-offs.",
    },
]


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


def load_csv(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def build_leader_reason(profile_key, tier_scope, row):
    critical_miss = row.get("critical_miss_rate") or row.get("critical_miss") or "0.0"
    if profile_key in ("high_safety", "balanced_soc"):
        return f"Profile leader under current constraints by Balanced OTS; {critical_miss}% Critical Miss; low review load."
    if tier_scope == "overall":
        return "Lowest False Review Load overall among models that cleared the guardrails; low review load."
    return "Lowest False Review Load in this tier among models that cleared the guardrails; low review load."


def build_overall_leaders(model_lookup):
    leaders = []
    for profile_key in PROFILE_ORDER:
        rows = load_csv(PROFILE_META[profile_key]["file"])
        if not rows:
            continue
        top = rows[0]
        model_name = top["model"]
        model = model_lookup.get(model_name, {})
        leaders.append(
            {
                "profile_key": profile_key,
                "profile_label": PROFILE_META[profile_key]["label"],
                "use_case": PROFILE_META[profile_key]["use_case"],
                "model": model_name,
                "tier": model.get("tier", "baseline"),
                "reason": build_leader_reason(profile_key, "overall", top),
            }
        )
    return leaders


def build_tier_leaders(model_lookup):
    grouped = {key: [] for key in TIER_LABELS}
    for row in load_csv(OPERATIONAL_SUMMARY_BY_TIER_PATH):
        tier_key = TIER_KEY_BY_SUMMARY_LABEL.get(row["tier"])
        profile_key = next(
            key for key, meta in PROFILE_META.items() if meta["label"] == row["profile"]
        )
        model_name = row["recommended_model"]
        model = model_lookup.get(model_name, {})
        grouped[tier_key].append(
            {
                "profile_key": profile_key,
                "profile_label": PROFILE_META[profile_key]["label"],
                "use_case": PROFILE_META[profile_key]["use_case"],
                "model": model_name,
                "tier": model.get("tier", tier_key),
                "reason": build_leader_reason(profile_key, "tier", row),
            }
        )

    for tier_key in grouped:
        grouped[tier_key].sort(key=lambda row: PROFILE_ORDER.index(row["profile_key"]))

    return grouped


def copy_gallery_charts():
    DOCS_CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    for chart in CHART_GALLERY:
        src = REPO_ROOT / "charts" / chart["filename"]
        dst = DOCS_CHARTS_DIR / chart["filename"]
        shutil.copy2(src, dst)


def main():
    rows = json.loads(LEADERBOARD_PATH.read_text())
    pricing_snapshot = load_pricing_snapshot()

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
            "estimated_run_cost_cents": estimate_run_cost_cents(
                row["model"], parse_int(row.get("total_tokens")), pricing_snapshot
            ),
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

    model_lookup = {row["model"]: row for row in models}
    copy_gallery_charts()

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "leaderboard": str(LEADERBOARD_PATH.relative_to(REPO_ROOT)),
            "operational_summary_by_tier": str(
                OPERATIONAL_SUMMARY_BY_TIER_PATH.relative_to(REPO_ROOT)
            ),
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
                "label": "Quality Score",
                "direction": "higher",
                "format": "percent",
                "description": "Plain-language label for the benchmark's confidence-weighted score (CW%) used in the README and blog posts.",
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
                "key": "estimated_run_cost_cents",
                "label": "Estimated Run Cost (¢)",
                "direction": "lower",
                "format": "currency_cents",
                "description": "Estimated benchmark-run cost based on total token usage and the committed OpenRouter pricing snapshot.",
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
                "key": "cw-vs-balanced-ots",
                "label": "Quality Score vs Balanced OTS",
                "x": "cw_pct",
                "y": "balanced_ots",
                "x_scale": "linear",
            },
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
                "key": "cw-vs-speed",
                "label": "Quality Score vs Speed",
                "x": "avg_seconds_per_event",
                "y": "cw_pct",
                "x_scale": "log",
            },
            {
                "key": "cw-vs-cost",
                "label": "Quality Score vs Cost",
                "x": "estimated_run_cost_cents",
                "y": "cw_pct",
                "x_scale": "linear",
            },
            {
                "key": "cw-vs-mae",
                "label": "Quality Score vs MAE",
                "x": "mae",
                "y": "cw_pct",
                "x_scale": "linear",
            },
        ],
        "leaders": {
            "overall": build_overall_leaders(model_lookup),
            "by_tier": build_tier_leaders(model_lookup),
            "tier_labels": TIER_LABELS,
        },
        "chart_gallery": [
            {
                **chart,
                "image_path": f"charts/{chart['filename']}",
            }
            for chart in CHART_GALLERY
        ],
        "models": models,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
