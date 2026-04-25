#!/usr/bin/env python3
"""Generate leaderboard charts for THOR AI Benchmarks."""

import json
import csv
import sys
from pathlib import Path

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    import numpy as np
except ImportError:
    print("matplotlib + numpy required: pip install matplotlib numpy")
    sys.exit(1)

# Load data
combined_dir = Path(__file__).parent.parent / "combined"
csv_path = combined_dir / "leaderboard.csv"
json_path = combined_dir / "leaderboard.json"
charts_dir = Path(__file__).parent.parent / "charts"
charts_dir.mkdir(exist_ok=True)

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

# Convert types
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

# Sort by CW% descending
models.sort(key=lambda x: x['cw_pct'], reverse=True)

# ── Chart 1: CW% Leaderboard ──────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 8))
names = [m['model'] for m in models]
cw = [m['cw_pct'] for m in models]
colors = plt.cm.RdYlGn([v/100 for v in cw])

bars = ax.barh(range(len(names)), cw, color=colors, edgecolor='white', linewidth=0.5)
ax.set_yticks(range(len(names)))
ax.set_yticklabels(names, fontsize=10)
ax.invert_yaxis()
ax.set_xlabel('Confidence-Weighted Score (%)', fontsize=12)
ax.set_title('THOR Finding Triage — CW% Leaderboard', fontsize=14, fontweight='bold')
ax.set_xlim(0, 55)

for i, (bar, val) in enumerate(zip(bars, cw)):
    ax.text(val + 0.5, i, f'{val:.1f}%', va='center', fontsize=9, fontweight='bold')

plt.tight_layout()
fig.savefig(charts_dir / 'cw-leaderboard.png', dpi=150, bbox_inches='tight')
print(f"✓ {charts_dir / 'cw-leaderboard.png'}")

# ── Chart 2: CW% vs MAE Scatter ───────────────────────────────
fig, ax = plt.subplots(figsize=(10, 8))
cw_vals = [m['cw_pct'] for m in models]
mae_vals = [m['mae'] for m in models]
scatter = ax.scatter(mae_vals, cw_vals, s=100, c=cw_vals, cmap='RdYlGn', edgecolors='gray', linewidths=0.5, zorder=5)

for m in models:
    ax.annotate(m['model'], (m['mae'], m['cw_pct']),
                textcoords="offset points", xytext=(5, 5), fontsize=8,
                alpha=0.85)

ax.set_xlabel('MAE (lower is better →)', fontsize=12)
ax.set_ylabel('CW% (higher is better ↑)', fontsize=12)
ax.set_title('CW% vs MAE — Top-Right is Best', fontsize=14, fontweight='bold')
ax.axhline(y=50, color='gray', linestyle='--', alpha=0.3)
ax.axvline(x=25, color='gray', linestyle='--', alpha=0.3)

plt.tight_layout()
fig.savefig(charts_dir / 'cw-vs-mae.png', dpi=150, bbox_inches='tight')
print(f"✓ {charts_dir / 'cw-vs-mae.png'}")

# ── Chart 3: Classification Accuracy Breakdown ──────────────────
fig, ax = plt.subplots(figsize=(12, 8))
y_pos = range(len(names))
exact = [m['exact'] for m in models]
minor = [m['minor'] for m in models]
hard = [m['hard'] for m in models]

ax.barh(y_pos, exact, color='#2ecc71', label='Exact', edgecolor='white', linewidth=0.5)
ax.barh(y_pos, minor, left=exact, color='#f39c12', label='Minor miss', edgecolor='white', linewidth=0.5)
ax.barh(y_pos, hard, left=[e+m for e,m in zip(exact,minor)], color='#e74c3c', label='Hard miss', edgecolor='white', linewidth=0.5)

ax.set_yticks(y_pos)
ax.set_yticklabels(names, fontsize=10)
ax.invert_yaxis()
ax.set_xlabel('Number of Findings', fontsize=12)
ax.set_title('Classification Accuracy Breakdown', fontsize=14, fontweight='bold')
ax.legend(loc='lower right', fontsize=10)

plt.tight_layout()
fig.savefig(charts_dir / 'classification-breakdown.png', dpi=150, bbox_inches='tight')
print(f"✓ {charts_dir / 'classification-breakdown.png'}")

print(f"\nGenerated 3 charts in {charts_dir}")