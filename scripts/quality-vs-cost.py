#!/usr/bin/env python3
"""Generate quality-vs-cost scatter chart for THOR benchmarks.

Reads leaderboard data and exclusion list from model_tiers.json,
uses the committed OpenRouter pricing snapshot, and produces charts/quality-vs-cost.png.
"""
import json, sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from openrouter_costs import BENCH_TO_OPENROUTER, INPUT_RATIO, OUTPUT_RATIO, load_pricing_snapshot

REPO_ROOT = Path(__file__).resolve().parent.parent
COMBINED_DIR = REPO_ROOT / "combined"
CHARTS_DIR = REPO_ROOT / "charts"
TIERS_PATH = REPO_ROOT / "scripts" / "model_tiers.json"


def main():
    # Load exclusion list from model_tiers.json
    with open(TIERS_PATH) as f:
        tiers_config = json.load(f)
    excluded = set(tiers_config.get("excluded", []))

    # Load tier lookup
    tier_lookup = {}
    tier_names = list(tiers_config.get("tiers", {}).keys())
    for tier_key, tier_data in tiers_config.get("tiers", {}).items():
        for m in tier_data["models"]:
            tier_lookup[m] = tier_key

    # Load committed pricing snapshot.
    or_pricing = load_pricing_snapshot()

    # Build price lookup for benchmark models
    model_prices = {}
    for name, or_id in BENCH_TO_OPENROUTER.items():
        if name in excluded:
            continue
        if or_id in or_pricing:
            model_prices[name] = or_pricing[or_id]

    # Load leaderboard
    lb_path = COMBINED_DIR / "leaderboard.json"
    with open(lb_path) as f:
        lb = json.load(f)

    results = []
    missing_price = []
    for m in lb:
        name = m['model']
        if name in excluded:
            continue
        cw_pct = float(m['cw_pct'])
        tier = m['tier']
        total_tokens = int(m.get('total_tokens', 0))
        if name not in model_prices:
            missing_price.append(name)
            continue
        p = model_prices[name]
        total_input = total_tokens * INPUT_RATIO
        total_output = total_tokens * OUTPUT_RATIO
        cost = (total_input * p['prompt']) + (total_output * p['completion'])
        cost_cents = cost * 100
        results.append({'model': name, 'cw_pct': cw_pct, 'cost_cents': cost_cents, 'tier': tier})
    if missing_price:
        print(f"  Warning: no OpenRouter pricing for {len(missing_price)} models: {missing_price}")

    # Generate chart
    tier_colors = {'closed_source': '#e74c3c', 'open_source_pro': '#3498db', 'open_source_consumer': '#2ecc71'}
    tier_markers = {'closed_source': 'D', 'open_source_pro': 's', 'open_source_consumer': 'o'}
    fig, ax = plt.subplots(figsize=(14, 10))

    for tier, color in tier_colors.items():
        tier_data = [r for r in results if r['tier'] == tier]
        x = [r['cost_cents'] for r in tier_data]
        y = [r['cw_pct'] for r in tier_data]
        ax.scatter(x, y, c=color, label=tier.replace('_', ' ').title(),
                   s=120, alpha=0.75, marker=tier_markers[tier])
        for r in tier_data:
            ax.annotate(r['model'], (r['cost_cents'], r['cw_pct']),
                        fontsize=7.5, ha='left', va='bottom',
                        xytext=(3, 3), textcoords='offset points')

    n_models = len(results)
    ax.set_xlabel('Estimated Cost per Run (¢)', fontsize=12)
    ax.set_ylabel('Quality Score (CW %)', fontsize=12)
    ax.set_title(f'THOR Benchmark: Quality vs Cost\n({n_models} models · cost based on actual token usage)', fontsize=14)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.08), ncol=3, framealpha=0.9)
    ax.grid(True, alpha=0.3)
    ax.axhline(y=38, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
    ax.axvline(x=5, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
    box = dict(boxstyle='round,pad=0.35', facecolor='white', edgecolor='lightgray', alpha=0.86)
    ax.text(0.02, 0.97, 'Upper-left\nbest cost/quality', transform=ax.transAxes, ha='left', va='top', fontsize=8.5, bbox=box)
    ax.text(0.98, 0.97, 'Upper-right\nhigh quality, expensive', transform=ax.transAxes, ha='right', va='top', fontsize=8.5, bbox=box)
    ax.text(0.02, 0.03, 'Lower-left\ncheap but weak', transform=ax.transAxes, ha='left', va='bottom', fontsize=8.5, bbox=box)
    ax.text(0.98, 0.03, 'Lower-right\nexpensive and weak', transform=ax.transAxes, ha='right', va='bottom', fontsize=8.5, bbox=box)
    plt.tight_layout()

    CHARTS_DIR.mkdir(exist_ok=True)
    fig.savefig(CHARTS_DIR / 'quality-vs-cost.png', dpi=150)
    print(f"✓ quality-vs-cost.png ({n_models} models, excluded: {excluded})")


if __name__ == "__main__":
    main()
