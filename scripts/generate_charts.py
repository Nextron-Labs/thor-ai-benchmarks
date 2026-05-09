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
    # Skip baselines (rank='baseline')
    if m.get('rank') == 'baseline':
        m['rank'] = 999999  # placeholder for filtering
        m['cw_pct'] = float(m['cw_pct'])
        m['ord_pct'] = float(m.get('ord_pct', 0))
        m['tier'] = 'baseline'
        continue
    
    m['rank'] = int(m.get('rank', 0))
    m['cw_pct'] = float(m['cw_pct'])
    m['ord_pct'] = float(m['ord_pct'])
    m['mae'] = float(m['mae']) if m.get('mae') and m['mae'] not in ('–', '-', '') else 99.0
    m['rmse'] = float(m['rmse']) if m.get('rmse') and m['rmse'] not in ('–', '-', '') else 99.0
    m['exact'] = int(m.get('exact', 0))
    m['minor'] = int(m.get('minor', 0))
    m['hard'] = int(m.get('hard', 0))
    m['n'] = int(m.get('n', 0))
    m['n_errors'] = int(m.get('n_errors', 0))
    m['incomplete'] = m.get('incomplete', False) in (True, 'True', 'true', 1)
    m['tier'] = tier_lookup.get(m['model'], 'closed_source')

# Sort: complete models by CW% descending, then incomplete models at bottom
# Exclude baselines from charts
models_filtered = [m for m in models if m.get('tier') != 'baseline']
complete = [m for m in models_filtered if not m.get('incomplete')]
incomplete_models = [m for m in models_filtered if m.get('incomplete')]
complete.sort(key=lambda x: x['cw_pct'], reverse=True)
incomplete_models.sort(key=lambda x: x['cw_pct'], reverse=True)
models = complete + incomplete_models

def tier_style(tier_key):
    t = tiers_config[tier_key]
    return t['color'], t['marker'], t['label']

def tier_models(models_list, tier_key):
    return [m for m in models_list if m['tier'] == tier_key]

# ── Chart 1: CW% Leaderboard (with tier colors + n annotations) ──────────────
fig, ax = plt.subplots(figsize=(14, 11))
names = [f"{m['model']} ⚠" if m.get('incomplete') else m['model'] for m in models]
cw = [m['cw_pct'] for m in models]
bar_colors = [tiers_config[m['tier']]['color'] for m in models]
n_vals = [int(m['n']) for m in models]
n_max = max(n_vals) if n_vals else 1

bars = ax.barh(range(len(names)), cw, color=bar_colors, edgecolor='white', linewidth=0.5)
ax.set_yticks(range(len(names)))
ax.set_yticklabels(names, fontsize=10)
ax.invert_yaxis()
ax.set_xlabel('Confidence-Weighted Score (%)', fontsize=12)
ax.set_title('THOR Finding Triage — CW% Leaderboard by Model Tier', fontsize=14, fontweight='bold')
max_cw = max(cw) if cw else 50
ax.set_xlim(0, max(max_cw * 1.15, 10))

for i, (bar, val, n) in enumerate(zip(bars, cw, n_vals)):
    n_label = f'{val:.1f}% (n={n})' if n < n_max else f'{val:.1f}%'
    ax.text(val + 0.5, i, n_label, va='center', fontsize=9, fontweight='bold')

# Legend
legend_patches = [mpatches.Patch(color=tiers_config[t]['color'], label=tiers_config[t]['label']) for t in tier_names]
legend_patches.append(mpatches.Patch(color='white', edgecolor='gray', label=f'⚠ = incomplete (n < {n_max})'))
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
ax.set_title('CW% vs MAE by Model Tier — Top-Left is Best', fontsize=14, fontweight='bold')
ax.legend(loc='lower left', fontsize=10, framealpha=0.9)
ax.axhline(y=45, color='gray', linestyle='--', alpha=0.3)
ax.axvline(x=25, color='gray', linestyle='--', alpha=0.3)

plt.tight_layout()
fig.savefig(charts_dir / 'cw-vs-mae.png', dpi=150, bbox_inches='tight')
print(f"✓ cw-vs-mae.png")

# ── Chart 3: Classification Breakdown ──────────────────────────
# This chart intentionally separates ordinal closeness from operationally
# different error types. TP→FP critical misses and FP→TP over-calls are shown
# as separate bars, not merged into a generic red "hard miss" bucket.
fig, (ax1, ax2) = plt.subplots(
    ncols=2, sharey=True, figsize=(18, 12),
    gridspec_kw={'width_ratios': [1.45, 1.0]}
)
y_pos = range(len(names))
exact = [m['exact'] for m in models]
minor = [m['minor'] for m in models]
hard = [m['hard'] for m in models]
critical_miss = [int(m.get('hard_miss', 0)) for m in models]   # TP→FP
false_escalation = [int(m.get('hard_over', 0)) for m in models]  # FP→TP
n_errors = [int(m.get('n_errors', 0)) for m in models]

# ── Total GT findings count ──
n_findings_total = 154  # R1=16 + R2=7 + R3=20 + R4=6 + R5=23 + R6=67 + R7=15
gap = [max(0, n_findings_total - int(m['n']) - ne) for m, ne in zip(models, n_errors)]

# Left panel: ordinal distance only. Use neutral colors; do not imply every
# >1-step miss has the same operational severity.
base1 = [e + mi for e, mi in zip(exact, minor)]
ax1.barh(y_pos, exact, color='#2ECC71', edgecolor='white', linewidth=0.5, label='Exact match')
ax1.barh(y_pos, minor, left=exact, color='#3498DB', edgecolor='white', linewidth=0.5, label='One-step away')
ax1.barh(y_pos, hard, left=base1, color='#7F8C8D', edgecolor='white', linewidth=0.5, label='More than one step away')
ax1.set_yticks(y_pos)
ax1.set_yticklabels(names, fontsize=9)
ax1.invert_yaxis()
ax1.set_xlabel('Findings by ordinal distance', fontsize=11)
ax1.set_xlim(0, n_findings_total)
ax1.set_title('A. Classification closeness', fontsize=13, fontweight='bold')
ax1.legend(loc='lower right', fontsize=9, framealpha=0.9)
ax1.grid(axis='x', alpha=0.2)

# Right panel: operationally important error types, separated.
h = 0.18
bars_cm = ax2.barh([i - 1.5*h for i in y_pos], critical_miss, height=h, color='#C0392B', label='Critical miss: TP→FP')
bars_fe = ax2.barh([i - 0.5*h for i in y_pos], false_escalation, height=h, color='#F39C12', label='Over-call: FP→TP')
bars_err = ax2.barh([i + 0.5*h for i in y_pos], n_errors, height=h, color='#95A5A6', label='LLM error')
bars_gap = ax2.barh([i + 1.5*h for i in y_pos], gap, height=h, color='#D5DBDB', label='Coverage gap')
for bars in (bars_cm, bars_fe, bars_err, bars_gap):
    for bar in bars:
        val = bar.get_width()
        if val > 0:
            ax2.text(val + 0.35, bar.get_y() + bar.get_height()/2, f'{int(val)}', va='center', ha='left', fontsize=7)
ax2.set_xlabel('Findings with operational impact', fontsize=11)
ax2.set_title('B. Critical error types kept separate', fontsize=13, fontweight='bold')
ax2.legend(loc='upper right', fontsize=9, framealpha=0.9)
ax2.grid(axis='x', alpha=0.2)
max_error = max(max(critical_miss), max(false_escalation), max(n_errors), max(gap), 1)
ax2.set_xlim(0, max_error * 1.25)
ax2.text(
    0.02, 0.02,
    'TP→FP suppresses a real incident. FP→TP escalates a false positive.\n'
    'They are intentionally not shown as the same error class.',
    transform=ax2.transAxes, fontsize=9, ha='left', va='bottom',
    bbox=dict(boxstyle='round,pad=0.35', facecolor='white', edgecolor='lightgray', alpha=0.9)
)

fig.suptitle('Classification Breakdown by Model', fontsize=15, fontweight='bold')
plt.tight_layout(rect=[0, 0, 1, 0.98])
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
    names_t = [f"{m['model']} ⚠" if m.get('incomplete') else m['model'] for m in tm]
    cw_t = [m['cw_pct'] for m in tm]

    bars = ax.barh(range(len(names_t)), cw_t, color=color, edgecolor='white', linewidth=0.5)
    ax.set_yticks(range(len(names_t)))
    ax.set_yticklabels(names_t, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel('CW%', fontsize=12)
    ax.set_title(f'{label} — CW%', fontsize=13, fontweight='bold')
    max_cw_t = max(cw_t) if cw_t else 50
    ax.set_xlim(0, max(max_cw_t * 1.12, 10))

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
    names_t = [f"{m['model']} ⚠" if m.get('incomplete') else m['model'] for m in tm]
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