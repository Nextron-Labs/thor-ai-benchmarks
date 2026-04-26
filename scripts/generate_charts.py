#!/usr/bin/env python3
"""Generate leaderboard charts for THOR AI Benchmarks with model tier markers."""

import json
import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Paths
repo_root = Path(__file__).resolve().parent.parent
combined_dir = repo_root / "combined"
csv_path = combined_dir / "leaderboard.csv"
json_path = combined_dir / "leaderboard.json"
charts_dir = repo_root / "charts"
charts_dir.mkdir(exist_ok=True)
tiers_path = Path(__file__).resolve().parent / "model_tiers.json"

# Load data
if json_path.exists():
    with open(json_path) as f:
        models = json.load(f)
elif csv_path.exists():
    models = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            models.append(row)
else:
    print("No leaderboard data found")
    sys.exit(1)

# Load tiers
with open(tiers_path) as f:
    tiers_config = json.load(f)["tiers"]

# Build tier lookup
tier_lookup = {}
tier_names = list(tiers_config.keys())
for tier_key, tier_data in tiers_config.items():
    for m in tier_data["models"]:
        tier_lookup[m] = tier_key

# Convert types and assign tiers
for m in models:
    m['rank'] = int(m.get('rank', 0))
    m['cw_pct'] = float(m['cw_pct'])
    m['ord_pct'] = float(m['ord_pct'])
    m['mae'] = float(m['mae'])
    m['rmse'] = float(m['rmse'])
    m['exact'] = int(m.get('exact', 0))
    m['minor'] = int(m.get('minor', 0))
    m['hard'] = int(m.get('hard', 0))
    m['n'] = int(m.get('n', 0))
    m['tier'] = tier_lookup.get(m['model'], 'closed_source')

# Sort by CW% descending
models.sort(key=lambda x: x['cw_pct'], reverse=True)

def tier_style(tier_key):
    t = tiers_config[tier_key]
    return t['color'], t['marker'], t['label']

def tier_models(models_list, tier_key):
    return [m for m in models_list if m['tier'] == tier_key]

# ── Chart 1: CW% Leaderboard (with tier colors) ──────────────
fig, ax = plt.subplots(figsize=(14, 9))
names = [m['model'] for m in models]
cw = [m['cw_pct'] for m in models]
bar_colors = [tiers_config[m['tier']]['color'] for m in models]

bars = ax.barh(range(len(names)), cw, color=bar_colors, edgecolor='white', linewidth=0.5)
ax.set_yticks(range(len(names)))
ax.set_yticklabels(names, fontsize=10)
ax.invert_yaxis()
ax.set_xlabel('Confidence-Weighted Score (%)', fontsize=12)
ax.set_title('THOR Finding Triage — CW% Leaderboard by Model Tier', fontsize=14, fontweight='bold')
ax.set_xlim(0, 55)

for i, (bar, val) in enumerate(zip(bars, cw)):
    ax.text(val + 0.5, i, f'{val:.1f}%', va='center', fontsize=9, fontweight='bold')

# Legend
legend_patches = [mpatches.Patch(color=tiers_config[t]['color'], label=tiers_config[t]['label']) for t in tier_names]
ax.legend(handles=legend_patches, loc='lower right', fontsize=10, framealpha=0.9)

plt.tight_layout()
fig.savefig(charts_dir / 'cw-leaderboard.png', dpi=150, bbox_inches='tight')
print(f"✓ cw-leaderboard.png")

# ── Chart 2: CW% vs MAE Scatter (with tier markers) ───────────
fig, ax = plt.subplots(figsize=(11, 9))

for tier_key in tier_names:
    tm = tier_models(models, tier_key)
    if not tm:
        continue
    color, marker, label = tier_style(tier_key)
    ax.scatter(
        [m['mae'] for m in tm],
        [m['cw_pct'] for m in tm],
        s=120, c=color, marker=marker, label=label,
        edgecolors='gray', linewidths=0.5, zorder=5
    )
    for m in tm:
        ax.annotate(m['model'], (m['mae'], m['cw_pct']),
                    textcoords="offset points", xytext=(6, 4), fontsize=8, alpha=0.85)

ax.set_xlabel('MAE (lower is better →)', fontsize=12)
ax.set_ylabel('CW% (higher is better ↑)', fontsize=12)
ax.set_title('CW% vs MAE by Model Tier — Top-Right is Best', fontsize=14, fontweight='bold')
ax.legend(loc='lower left', fontsize=10, framealpha=0.9)
ax.axhline(y=45, color='gray', linestyle='--', alpha=0.3)
ax.axvline(x=25, color='gray', linestyle='--', alpha=0.3)

plt.tight_layout()
fig.savefig(charts_dir / 'cw-vs-mae.png', dpi=150, bbox_inches='tight')
print(f"✓ cw-vs-mae.png")

# ── Chart 3: Classification Breakdown (with tier colors + miss/over split) ──────
fig, ax = plt.subplots(figsize=(14, 9))
y_pos = range(len(names))
exact = [m['exact'] for m in models]
minor = [m['minor'] for m in models]
hard_miss = [int(m.get('hard_miss', 0)) for m in models]   # TP→FP: missed real threat
hard_over = [int(m.get('hard_over', 0)) for m in models]  # FP→TP: over-called non-threat

# Use tier color for the exact-match bar, lighter shade for minor
tier_colors_light = {
    'closed_source': '#F1948A',
    'open_source_pro': '#85C1E9',
    'open_source_consumer': '#82E0AA',
}

ax.barh(y_pos, exact, color=bar_colors, edgecolor='white', linewidth=0.5)
ax.barh(y_pos, minor, left=exact, color=[tier_colors_light[m['tier']] for m in models], edgecolor='white', linewidth=0.5)
ax.barh(y_pos, hard_miss, left=[e+m for e,m in zip(exact,minor)], color='#C0392B', edgecolor='white', linewidth=0.5, label='_nolegend_')  # Dark red: missed threats
ax.barh(y_pos, hard_over, left=[e+m+h for e,m,h in zip(exact,minor,hard_miss)], color='#E67E22', edgecolor='white', linewidth=0.5, alpha=0.85, label='_nolegend_')  # Orange: overcalls

ax.set_yticks(y_pos)
ax.set_yticklabels(names, fontsize=10)
ax.invert_yaxis()
ax.set_xlabel('Number of Findings', fontsize=12)
ax.set_title('Classification Accuracy Breakdown by Model Tier', fontsize=14, fontweight='bold')

# Custom legend
legend_items = [mpatches.Patch(color=tiers_config[t]['color'], label=tiers_config[t]['label']) for t in tier_names]
legend_items += [
    mpatches.Patch(color='gray', label='Exact match'),
    mpatches.Patch(color='#F1948A', label='Minor miss (1 step)'),
    mpatches.Patch(color='#C0392B', label='Missed threat (TP→FP)'),
    mpatches.Patch(color='#E67E22', alpha=0.85, label='Over-call (FP→TP)'),
]
ax.legend(handles=legend_items, loc='lower right', fontsize=9, framealpha=0.9)

plt.tight_layout()
fig.savefig(charts_dir / 'classification-breakdown.png', dpi=150, bbox_inches='tight')
print(f"✓ classification-breakdown.png")

# ── Per-Tier CW% Charts ────────────────────────────────────────
for tier_key in tier_names:
    tm = tier_models(models, tier_key)
    if not tm:
        continue
    color, marker, label = tier_style(tier_key)
    short_name = tier_key.replace('_', '-')

    fig, ax = plt.subplots(figsize=(10, max(4, len(tm) * 0.5 + 1)))
    tm.sort(key=lambda x: x['cw_pct'], reverse=True)
    names_t = [m['model'] for m in tm]
    cw_t = [m['cw_pct'] for m in tm]

    bars = ax.barh(range(len(names_t)), cw_t, color=color, edgecolor='white', linewidth=0.5)
    ax.set_yticks(range(len(names_t)))
    ax.set_yticklabels(names_t, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel('CW%', fontsize=12)
    ax.set_title(f'{label} — CW%', fontsize=13, fontweight='bold')
    ax.set_xlim(0, 55)

    for i, (bar, val) in enumerate(zip(bars, cw_t)):
        ax.text(val + 0.3, i, f'{val:.1f}%', va='center', fontsize=9, fontweight='bold')

    plt.tight_layout()
    fig.savefig(charts_dir / f'cw-{short_name}.png', dpi=150, bbox_inches='tight')
    print(f"✓ cw-{short_name}.png")

# ── Per-Tier MAE Charts ────────────────────────────────────────
for tier_key in tier_names:
    tm = tier_models(models, tier_key)
    if not tm:
        continue
    color, marker, label = tier_style(tier_key)
    short_name = tier_key.replace('_', '-')

    fig, ax = plt.subplots(figsize=(10, max(4, len(tm) * 0.5 + 1)))
    tm.sort(key=lambda x: x['mae'])
    names_t = [m['model'] for m in tm]
    mae_t = [m['mae'] for m in tm]

    bars = ax.barh(range(len(names_t)), mae_t, color=color, edgecolor='white', linewidth=0.5, alpha=0.85)
    ax.set_yticks(range(len(names_t)))
    ax.set_yticklabels(names_t, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel('MAE (lower is better)', fontsize=12)
    ax.set_title(f'{label} — MAE', fontsize=13, fontweight='bold')
    ax.set_xlim(0, 35)

    for i, (bar, val) in enumerate(zip(bars, mae_t)):
        ax.text(val + 0.3, i, f'{val:.1f}', va='center', fontsize=9, fontweight='bold')

    plt.tight_layout()
    fig.savefig(charts_dir / f'mae-{short_name}.png', dpi=150, bbox_inches='tight')
    print(f"✓ mae-{short_name}.png")

print(f"\nDone — {3 + 2*len(tier_names)} charts in {charts_dir}")