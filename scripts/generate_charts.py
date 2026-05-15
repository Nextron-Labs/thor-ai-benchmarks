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
    tiers_payload = json.load(f)
tiers_config = tiers_payload["tiers"]
excluded = set(tiers_payload.get("excluded", []))

# Build tier lookup
tier_lookup = {}
tier_names = list(tiers_config.keys())
for tier_key, tier_data in tiers_config.items():
    for m in tier_data["models"]:
        tier_lookup[m] = tier_key


def resolve_tier(model_row):
    if model_row.get("tier") in tiers_config:
        return model_row["tier"]
    if model_row["model"] in tier_lookup:
        return tier_lookup[model_row["model"]]
    raise SystemExit(
        f"Model {model_row['model']} is missing a known tier in leaderboard data and scripts/model_tiers.json"
    )

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
    m['tier'] = resolve_tier(m)

# Public charts must contain complete, publishable model results only.
# Incomplete/errored attempts are documented separately, never plotted/ranked.
models = [
    m
    for m in models
    if m.get('tier') != 'baseline'
    and m['model'] not in excluded
    and not m.get('incomplete')
    and int(m.get('n_errors', 0)) == 0
]
models.sort(key=lambda x: x['cw_pct'], reverse=True)

def tier_style(tier_key):
    t = tiers_config[tier_key]
    return t['color'], t['marker'], t['label']

def tier_models(models_list, tier_key):
    return [m for m in models_list if m['tier'] == tier_key]

# ── Chart 1: CW% Leaderboard (with tier colors + n annotations) ──────────────
fig, ax = plt.subplots(figsize=(14, 11))
names = [m['model'] for m in models]
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
# Operational classification categories. Bars are normalized to each complete
# model's current full report set. Public artifacts exclude incomplete runs, so
# LLM error counts should remain zero; the grey category is kept only as a guard.
combined_results = json.load(open(combined_dir / 'results-combined.json'))
report_key = max((key.split('/')[-1] for key in combined_results if '+' in key.split('/')[-1]), key=lambda r: (r.count('+') + 1, r))

cats = [
    ('exact', 'Exact match', '#2ECC71'),
    ('minor', 'Minor miss', '#3498DB'),
    ('over_call', 'Over-call (FP→TP)', '#F39C12'),
    ('critical_miss', 'Critical miss (TP→FP)', '#8B0000'),
    ('anomaly_suppression', 'Anomaly suppression (Inc→FP)', '#8E44AD'),
    ('llm_error', 'LLM error / invalid response', '#95A5A6'),
]

breakdown = []
for m in models:
    key = f"{m['model']}/{report_key}"
    cc = combined_results.get(key, {}).get('class_counts', {})
    exact_count = cc.get('FP-FP', 0) + cc.get('Inc-Inc', 0) + cc.get('TP-TP', 0)
    # One-step differences that are not broken out as operational suppression.
    minor_count = cc.get('FP-Inc', 0) + cc.get('TP-Inc', 0) + cc.get('Inc-TP', 0)
    over_call = cc.get('FP-TP', 0)
    critical_miss = cc.get('TP-FP', 0)
    anomaly_suppression = cc.get('Inc-FP', 0)
    llm_error = int(m.get('n_errors', 0))
    total = exact_count + minor_count + over_call + critical_miss + anomaly_suppression + llm_error
    # Fallback to leaderboard aggregates if class_counts are unavailable.
    if total == 0:
        exact_count = int(m.get('exact', 0))
        over_call = int(m.get('hard_over', 0))
        critical_miss = int(m.get('hard_miss', 0))
        llm_error = int(m.get('n_errors', 0))
        minor_count = max(0, int(m.get('n', 0)) - exact_count - over_call - critical_miss)
        anomaly_suppression = 0
        total = exact_count + minor_count + over_call + critical_miss + anomaly_suppression + llm_error
    breakdown.append({
        'model': m['model'],
        'exact': exact_count,
        'minor': minor_count,
        'over_call': over_call,
        'critical_miss': critical_miss,
        'anomaly_suppression': anomaly_suppression,
        'llm_error': llm_error,
        'total': max(total, 1),
    })

if any(b['llm_error'] for b in breakdown):
    bad = ', '.join(b['model'] for b in breakdown if b['llm_error'])
    raise SystemExit(f'Public classification chart refuses incomplete/errored models: {bad}')

# Only show categories that actually occur. This keeps the legend honest as
# report/model coverage changes; zero-count categories should not imply visible
# bars. Exact/minor are kept because they are the core classification mass.
visible_cats = [
    c for c in cats
    if c[0] in ('exact', 'minor') or any(b[c[0]] > 0 for b in breakdown)
]

fig, ax = plt.subplots(figsize=(15, 12))
y_pos = range(len(names))
left = np.zeros(len(breakdown))
for key, label, color in visible_cats:
    vals = [100.0 * b[key] / b['total'] for b in breakdown]
    ax.barh(y_pos, vals, left=left, color=color, edgecolor='white', linewidth=0.45, label=label)
    left += np.array(vals)

ax.set_yticks(y_pos)
ax.set_yticklabels(names, fontsize=9)
ax.invert_yaxis()
ax.set_xlabel('Share of scored findings and invalid responses (%)', fontsize=12)
ax.set_xlim(0, 100)
ax.set_title('Classification Breakdown by Model — Operational Error Categories', fontsize=14, fontweight='bold')
ax.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=9, framealpha=0.94)
ax.grid(axis='x', alpha=0.2)
ax.text(
    0.01, 0.015,
    f'Bars sum to 100% per model over {report_key}. Incomplete model attempts are excluded from public charts.\n'
    'Minor miss excludes Inc→FP because anomaly suppression has distinct operational risk.',
    transform=ax.transAxes, fontsize=8.5, ha='left', va='bottom',
    bbox=dict(boxstyle='round,pad=0.35', facecolor='white', edgecolor='lightgray', alpha=0.9)
)
plt.tight_layout()
fig.savefig(charts_dir / 'classification-breakdown.png', dpi=150, bbox_inches='tight')
print(f"✓ classification-breakdown.png")

# Companion chart: operational errors only, absolute counts for easier comparison.
fig, ax = plt.subplots(figsize=(14, 12))
y_pos = range(len(names))
h = 0.20
error_keys = [
    ('over_call', 'Over-call (FP→TP)', '#F39C12', -1.5*h),
    ('critical_miss', 'Critical miss (TP→FP)', '#8B0000', -0.5*h),
    ('anomaly_suppression', 'Anomaly suppression (Inc→FP)', '#8E44AD', 0.5*h),
    ('llm_error', 'LLM error / invalid response', '#95A5A6', 1.5*h),
]
visible_error_keys = [e for e in error_keys if any(b[e[0]] > 0 for b in breakdown)]
for key, label, color, offset in visible_error_keys:
    vals = [b[key] for b in breakdown]
    bars = ax.barh([i + offset for i in y_pos], vals, height=h, color=color, label=label)
    for bar, val in zip(bars, vals):
        if val > 0:
            ax.text(val + 0.25, bar.get_y() + bar.get_height()/2, str(val), va='center', ha='left', fontsize=7)
ax.set_yticks(y_pos)
ax.set_yticklabels(names, fontsize=9)
ax.invert_yaxis()
ax.set_xlabel('Number of findings / invalid responses', fontsize=12)
ax.set_title('Operational Error Breakdown by Model', fontsize=14, fontweight='bold')
ax.legend(loc='lower right', fontsize=9, framealpha=0.94)
ax.grid(axis='x', alpha=0.2)
max_err = max(max(b[k] for b in breakdown) for k, *_ in visible_error_keys) if visible_error_keys else 0
ax.set_xlim(0, max_err * 1.25 if max_err else 1)
plt.tight_layout()
fig.savefig(charts_dir / 'operational-error-breakdown.png', dpi=150, bbox_inches='tight')
print(f"✓ operational-error-breakdown.png")

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
