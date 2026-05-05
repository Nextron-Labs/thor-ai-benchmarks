#!/usr/bin/env python3
"""Generate quality-vs-speed scatter chart for THOR benchmarks.

Reads leaderboard data and exclusion list from model_tiers.json,
uses avg_seconds_per_event from the leaderboard, and produces
charts/quality-vs-speed.png.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parent.parent
COMBINED_DIR = REPO_ROOT / "combined"
CHARTS_DIR = REPO_ROOT / "charts"
TIERS_PATH = REPO_ROOT / "scripts" / "model_tiers.json"


def main():
    # Load exclusion list from model_tiers.json
    with open(TIERS_PATH) as f:
        tiers_config = json.load(f)
    excluded = set(tiers_config.get("excluded", []))

    # Load leaderboard
    lb_path = COMBINED_DIR / "leaderboard.json"
    with open(lb_path) as f:
        lb = json.load(f)

    results = []
    for m in lb:
        name = m['model']
        if name in excluded:
            continue
        cw_pct = float(m['cw_pct'])
        tier = m['tier']
        avg_s = float(m.get('avg_seconds_per_event', 0))
        if avg_s <= 0:
            continue
        results.append({'model': name, 'cw_pct': cw_pct, 'avg_s': avg_s, 'tier': tier})

    # Generate chart
    tier_colors = {'closed_source': '#e74c3c', 'open_source_pro': '#3498db', 'open_source_consumer': '#2ecc71'}
    tier_markers = {'closed_source': 'D', 'open_source_pro': 's', 'open_source_consumer': 'o'}
    fig, ax = plt.subplots(figsize=(14, 10))

    for tier, color in tier_colors.items():
        tier_data = [r for r in results if r['tier'] == tier]
        x = [r['avg_s'] for r in tier_data]
        y = [r['cw_pct'] for r in tier_data]
        ax.scatter(x, y, c=color, label=tier.replace('_', ' ').title(),
                   s=120, alpha=0.75, marker=tier_markers[tier])
        for r in tier_data:
            ax.annotate(r['model'], (r['avg_s'], r['cw_pct']),
                        fontsize=7.5, ha='left', va='bottom',
                        xytext=(3, 3), textcoords='offset points')

    n_models = len(results)
    ax.set_xlabel('Average Time per Finding (seconds)', fontsize=12)
    ax.set_ylabel('Quality Score (CW %)', fontsize=12)
    ax.set_title(f'THOR Benchmark: Quality vs Speed\n({n_models} models · average wall-clock seconds per finding assessed)', fontsize=14)
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')
    from matplotlib.ticker import ScalarFormatter
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_formatter(ScalarFormatter())
    ax.set_xlim(left=0.8, right=200)
    ax.set_ylim(bottom=0)

    # Speed tier reference lines (log scale)
    ax.axvline(x=5, color='#27ae60', linestyle='--', alpha=0.4, linewidth=0.8)
    ax.axvline(x=15, color='#f39c12', linestyle='--', alpha=0.4, linewidth=0.8)
    ax.axvline(x=30, color='#e67e22', linestyle='--', alpha=0.4, linewidth=0.8)
    ax.axvline(x=60, color='#e74c3c', linestyle='--', alpha=0.4, linewidth=0.8)
    # Label speed zones
    ymin, ymax = ax.get_ylim()
    ax.text(2.5, ymax * 0.02, 'Fast (<5s)', fontsize=8, ha='center', color='#27ae60', alpha=0.7)
    ax.text(9, ymax * 0.02, 'Quick (5-15s)', fontsize=8, ha='center', color='#2ecc71', alpha=0.7)
    ax.text(21, ymax * 0.02, 'Moderate (15-30s)', fontsize=8, ha='center', color='#f39c12', alpha=0.7)
    ax.text(42, ymax * 0.02, 'Slow (30-60s)', fontsize=8, ha='center', color='#e67e22', alpha=0.7)
    ax.text(90, ymax * 0.02, 'Very Slow (60s+)', fontsize=8, ha='center', color='#e74c3c', alpha=0.7)

    # Quality reference line
    ax.axhline(y=50, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
    ax.text(ax.get_xlim()[1] * 0.98, 50.5, '50% CW', fontsize=8, ha='right', color='gray', alpha=0.7)

    plt.tight_layout()

    CHARTS_DIR.mkdir(exist_ok=True)
    fig.savefig(CHARTS_DIR / 'quality-vs-speed.png', dpi=150)
    print(f"✓ quality-vs-speed.png ({n_models} models, excluded: {excluded})")


if __name__ == "__main__":
    main()