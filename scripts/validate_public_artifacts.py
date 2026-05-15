#!/usr/bin/env python3
"""Validate public benchmark artifacts before publishing.

The public repo must never rank or plot partial model runs. Private benchmark
artifacts may keep failed attempts for debugging, but public leaderboard/results
must contain only models that completed the current full report set with zero
LLM errors.
"""
from __future__ import annotations

import json
from pathlib import Path

from openrouter_costs import estimate_run_cost_cents, load_pricing_snapshot

ROOT = Path(__file__).resolve().parents[1]
COMBINED = ROOT / "combined"
DOCS = ROOT / "docs"
README = ROOT / "README.md"
TIERS_PATH = ROOT / "scripts" / "model_tiers.json"

GENERATED_MARKERS = [
    "<!-- BEGIN GENERATED:CURRENT_RESULT_SUMMARY -->",
    "<!-- END GENERATED:CURRENT_RESULT_SUMMARY -->",
    "<!-- BEGIN GENERATED:FULL_DATA -->",
    "<!-- END GENERATED:FULL_DATA -->",
]


def load_json(path: Path):
    with path.open() as f:
        return json.load(f)


def main() -> int:
    leaderboard = load_json(COMBINED / "leaderboard.json")
    results = load_json(COMBINED / "results-combined.json")
    dropped_path = COMBINED / "dropped-models.json"
    dropped = load_json(dropped_path) if dropped_path.exists() else []
    tier_keys = set(load_json(TIERS_PATH)["tiers"])
    pricing_snapshot = load_pricing_snapshot()

    real_leaderboard = [m for m in leaderboard if m.get("rank") != "baseline"]
    bad_tiers = sorted(
        m["model"] for m in real_leaderboard if m.get("tier") not in tier_keys
    )
    if bad_tiers:
        raise SystemExit(f"Public leaderboard contains models with unknown tiers: {bad_tiers}")

    bad_lb = [
        m["model"] for m in real_leaderboard
        if m.get("incomplete") or int(m.get("n_errors", 0)) != 0
    ]
    if bad_lb:
        raise SystemExit(f"Public leaderboard contains incomplete/error models: {bad_lb}")

    dropped_models = {m["model"] for m in dropped}
    leaked = sorted({key.split("/")[0] for key in results if key.split("/")[0] in dropped_models})
    if leaked:
        raise SystemExit(f"Dropped models leaked into public results: {leaked}")

    full_report = max(
        (key.split("/")[-1] for key in results if "+" in key.split("/")[-1]),
        key=lambda r: (r.count("+") + 1, r),
    )
    combined_rows = {
        key.split("/")[0]: score
        for key, score in results.items()
        if key.endswith("/" + full_report)
    }
    expected_n = max((score.get("n_matched", 0) for score in combined_rows.values()), default=0)
    bad_results = []
    for model, score in combined_rows.items():
        if score.get("incomplete") or score.get("n_errors", 0) != 0 or score.get("n_matched") != expected_n:
            bad_results.append((model, score.get("n_matched"), score.get("n_errors"), score.get("incomplete")))
    if bad_results:
        raise SystemExit(f"Public combined results contain incomplete/error rows: {bad_results}")

    lb_models = {m["model"] for m in real_leaderboard}
    if set(combined_rows) != lb_models:
        raise SystemExit(
            "Leaderboard/result model mismatch: "
            f"leaderboard-only={sorted(lb_models - set(combined_rows))}, "
            f"results-only={sorted(set(combined_rows) - lb_models)}"
        )

    required_charts = [
        "classification-breakdown.png",
        "operational-error-breakdown.png",
        "cw-leaderboard.png",
        "critical-miss-vs-false-review.png",
        "balanced-ots-vs-false-review.png",
        "cw-vs-balanced-ots.png",
        "quality-vs-cost.png",
        "quality-vs-speed.png",
        "operational-profile-summary.png",
        "operational-profile-summary-by-tier.png",
    ]
    missing = [name for name in required_charts if not (ROOT / "charts" / name).exists()]
    if missing:
        raise SystemExit(f"Missing required charts: {missing}")

    site_artifacts = [
        DOCS / "data" / "leaderboard-explorer.json",
        DOCS / "charts" / "classification-breakdown.png",
        DOCS / "charts" / "quality-vs-cost.png",
        DOCS / "charts" / "quality-vs-speed.png",
        DOCS / "charts" / "operational-profile-summary.png",
        DOCS / "charts" / "operational-profile-summary-by-tier.png",
    ]
    missing_site = [str(path.relative_to(ROOT)) for path in site_artifacts if not path.exists()]
    if missing_site:
        raise SystemExit(f"Missing required site artifacts: {missing_site}")

    readme_text = README.read_text()
    missing_markers = [marker for marker in GENERATED_MARKERS if marker not in readme_text]
    if missing_markers:
        raise SystemExit(f"README is missing generated content markers: {missing_markers}")

    missing_cost = sorted(
        m["model"]
        for m in real_leaderboard
        if estimate_run_cost_cents(
            m["model"],
            int(m.get("total_tokens", 0)) if m.get("total_tokens") not in (None, "", "–", "-") else None,
            pricing_snapshot,
        )
        is None
    )
    if missing_cost:
        print(
            "WARNING: models without cost estimates will be omitted from cost-based views: "
            + ", ".join(missing_cost)
        )

    print(f"OK: public artifacts contain {len(lb_models)} complete models over {full_report} (n={expected_n})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
