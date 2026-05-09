#!/usr/bin/env python3
"""Generate operational profile CSVs and charts for THOR AI Benchmarks."""

import csv
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
COMBINED = ROOT / "combined"
CHARTS = ROOT / "charts"
CHARTS.mkdir(exist_ok=True)

# Profile table cost estimates used in OPERATIONAL_PROFILES.md/README.
# Local/free-tier models are shown as $0.00 marginal API cost.
COST_PER_RUN = {
    "llama-3.1-8b": 0.00,
    "gpt-5-nano": 0.12,
    "deepseek-v3.2": 0.32,
    "nemotron-3-nano-omni": 0.00,
    "llama-3.1-70b": 0.00,
    "qwen3-235b-a22b": 0.00,
    "minimax-m2.5": 0.16,
    "gpt-oss-120b": 0.00,
    "deepseek-v4-flash": 0.10,
    "gemma4-31b": 0.00,
    "grok-4.20": 2.23,
}

PROFILES = [
    {
        "name": "High-safety",
        "csv": "operational-profile-high-safety.csv",
        "requirements": lambda m: m["critical_miss"] <= 5 and m["threat_capture"] >= 95 and m["false_review"] < 100,
        "sort": lambda m: (-m["balanced_ots"], m["false_review"]),
    },
    {
        "name": "Balanced SOC",
        "csv": "operational-profile-balanced-soc.csv",
        "requirements": lambda m: m["critical_miss"] <= 15 and m["threat_capture"] >= 85 and m["false_review"] <= 75,
        "sort": lambda m: (-m["balanced_ots"], m["false_review"]),
    },
    {
        "name": "Noise-reduction",
        "csv": "operational-profile-noise-reduction.csv",
        "requirements": lambda m: m["false_review"] <= 55 and m["critical_miss"] <= 20 and m["balanced_ots"] > 0,
        "sort": lambda m: (m["false_review"], -m["balanced_ots"]),
    },
]

NUMERIC = {
    "cw_pct", "ots_pct", "ots_macro", "balanced_ots", "threat_capture", "critical_miss",
    "anomaly_capture", "anomaly_suppression", "false_review", "false_escalation",
    "ord_pct", "avg_seconds_per_event",
}
INTS = {"exact", "minor", "hard", "hard_miss", "hard_over", "n_errors", "n"}


def load_rows():
    """Load the CSV leaderboard and merge JSON-only fields such as avg_seconds_per_event."""
    json_rows = {}
    json_path = COMBINED / "leaderboard.json"
    if json_path.exists():
        with open(json_path) as f:
            json_rows = {r["model"]: r for r in json.load(f)}

    rows = []
    with open(COMBINED / "leaderboard.csv", newline="") as f:
        for row in csv.DictReader(f):
            if row["model"] in json_rows:
                for k, v in json_rows[row["model"]].items():
                    row.setdefault(k, v)
            for k in NUMERIC:
                if k in row and row[k] not in ("", "–", "-", None):
                    row[k] = float(row[k])
            for k in INTS:
                if k in row and row[k] not in ("", "–", "-", None):
                    row[k] = int(row[k])
            row["incomplete"] = str(row.get("incomplete", "False")).lower() == "true"
            rows.append(row)
    return rows


def write_profile_csvs(models):
    profile_rows = {}
    fields = ["rank", "model", "cw_pct", "balanced_ots", "critical_miss", "threat_capture", "false_review", "false_escalation", "cost_per_run", "avg_seconds_per_event", "n", "incomplete"]
    for profile in PROFILES:
        matched = [m for m in models if profile["requirements"](m)]
        matched.sort(key=profile["sort"])
        profile_rows[profile["name"]] = matched
        with open(COMBINED / profile["csv"], "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for i, m in enumerate(matched, 1):
                w.writerow({
                    "rank": i,
                    "model": m["model"],
                    "cw_pct": f"{m['cw_pct']:.1f}",
                    "balanced_ots": f"{m['balanced_ots']:.1f}",
                    "critical_miss": f"{m['critical_miss']:.1f}",
                    "threat_capture": f"{m['threat_capture']:.1f}",
                    "false_review": f"{m['false_review']:.1f}",
                    "false_escalation": f"{m['false_escalation']:.1f}",
                    "cost_per_run": f"{COST_PER_RUN.get(m['model'], math.nan):.2f}" if m['model'] in COST_PER_RUN else "",
                    "avg_seconds_per_event": f"{m.get('avg_seconds_per_event', 0):.2f}",
                    "n": m["n"],
                    "incomplete": m["incomplete"],
                })
    return profile_rows


def write_baseline_csv(baselines):
    fields = ["strategy", "cw_pct", "balanced_ots", "critical_miss", "threat_capture", "false_review", "false_escalation", "cost_per_run"]
    with open(COMBINED / "operational-baselines.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for name in ["always-fp", "always-inc", "always-tp"]:
            m = next(b for b in baselines if b["model"] == name)
            w.writerow({
                "strategy": name,
                "cw_pct": f"{m['cw_pct']:.1f}",
                "balanced_ots": f"{m['balanced_ots']:.1f}",
                "critical_miss": f"{m['critical_miss']:.1f}",
                "threat_capture": f"{m['threat_capture']:.1f}",
                "false_review": f"{m['false_review']:.1f}",
                "false_escalation": f"{m['false_escalation']:.1f}",
                "cost_per_run": "0.00",
            })


def plot_profile_summary(profile_rows, baselines):
    leaders = [(name, rows[0]) for name, rows in profile_rows.items() if rows]
    labels = [name for name, _ in leaders] + ["always-inc\nbaseline"]
    always_inc = next(b for b in baselines if b["model"] == "always-inc")
    points = [m for _, m in leaders] + [always_inc]
    x = np.arange(len(points))
    width = 0.25
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.bar(x - width, [p["balanced_ots"] for p in points], width, label="Balanced OTS", color="#3498db")
    ax.bar(x, [p["critical_miss"] for p in points], width, label="Critical Miss Rate", color="#e74c3c")
    ax.bar(x + width, [p["false_review"] for p in points], width, label="False Review Load", color="#95a5a6")
    for i, p in enumerate(points):
        ax.text(i, 103, p["model"].replace("always-", "always-\n"), ha="center", va="top", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 110)
    ax.set_ylabel("Percent")
    ax.set_title("Operational Profile Leaders vs Safe Baseline")
    ax.legend(loc="upper left")
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    fig.savefig(CHARTS / "operational-profile-summary.png", dpi=150)


def scatter_charts(models):
    leaders = {"llama-3.1-8b", "deepseek-v3.2", "deepseek-v4-flash"}
    colors = [m["critical_miss"] for m in models]
    sizes = [60 + max(m["balanced_ots"], 0) * 4 for m in models]

    fig, ax = plt.subplots(figsize=(12, 8))
    sc = ax.scatter([m["false_review"] for m in models], [m["critical_miss"] for m in models], c=[m["balanced_ots"] for m in models], cmap="viridis", s=sizes, alpha=0.75, edgecolors="gray", linewidths=0.5)
    for m in models:
        if m["model"] in leaders or (m["critical_miss"] <= 15 and m["false_review"] <= 75 and m["balanced_ots"] > 20):
            ax.annotate(m["model"], (m["false_review"], m["critical_miss"]), xytext=(5, 4), textcoords="offset points", fontsize=8)
    ax.axhline(5, color="#e74c3c", linestyle="--", linewidth=0.8, alpha=0.6)
    ax.axhline(15, color="#e67e22", linestyle="--", linewidth=0.8, alpha=0.6)
    ax.axvline(55, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.axvline(75, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.set_xlabel("False Review Load (%) — lower is less analyst review")
    ax.set_ylabel("Critical Miss Rate (%) — lower is safer")
    ax.set_title("Critical Miss Rate vs False Review Load")
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("Balanced OTS (%)")
    ax.grid(alpha=0.25)
    plt.tight_layout()
    fig.savefig(CHARTS / "critical-miss-vs-false-review.png", dpi=150)

    fig, ax = plt.subplots(figsize=(12, 8))
    sc = ax.scatter([m["false_review"] for m in models], [m["balanced_ots"] for m in models], c=colors, cmap="RdYlGn_r", s=120, alpha=0.75, edgecolors="gray", linewidths=0.5)
    for m in models:
        if m["model"] in leaders or m["balanced_ots"] >= 33:
            ax.annotate(m["model"], (m["false_review"], m["balanced_ots"]), xytext=(5, 4), textcoords="offset points", fontsize=8)
    ax.axvline(55, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.axvline(75, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.axhline(0, color="black", linewidth=0.8, alpha=0.5)
    ax.set_xlabel("False Review Load (%) — lower is better")
    ax.set_ylabel("Balanced OTS (%) — higher is better")
    ax.set_title("Balanced OTS vs False Review Load (color = Critical Miss Rate)")
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("Critical Miss Rate (%)")
    ax.grid(alpha=0.25)
    plt.tight_layout()
    fig.savefig(CHARTS / "balanced-ots-vs-false-review.png", dpi=150)

    fig, ax = plt.subplots(figsize=(12, 8))
    sc = ax.scatter([m["cw_pct"] for m in models], [m["balanced_ots"] for m in models], c=[m["critical_miss"] for m in models], cmap="RdYlGn_r", s=120, alpha=0.75, edgecolors="gray", linewidths=0.5)
    for m in models:
        if m["model"] in leaders or m["cw_pct"] >= 40 or m["balanced_ots"] >= 35:
            ax.annotate(m["model"], (m["cw_pct"], m["balanced_ots"]), xytext=(5, 4), textcoords="offset points", fontsize=8)
    ax.set_xlabel("CW% — confidence-weighted classification/score quality")
    ax.set_ylabel("Balanced OTS (%) — operational triage utility")
    ax.set_title("CW% vs Balanced OTS")
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label("Critical Miss Rate (%)")
    ax.grid(alpha=0.25)
    plt.tight_layout()
    fig.savefig(CHARTS / "cw-vs-balanced-ots.png", dpi=150)


def main():
    rows = load_rows()
    baselines = [r for r in rows if r["tier"] == "baseline"]
    models = [r for r in rows if r["tier"] != "baseline"]
    profile_rows = write_profile_csvs(models)
    write_baseline_csv(baselines)
    plot_profile_summary(profile_rows, baselines)
    scatter_charts(models)
    print("✓ operational profile CSVs")
    print("✓ operational-profile-summary.png")
    print("✓ critical-miss-vs-false-review.png")
    print("✓ balanced-ots-vs-false-review.png")
    print("✓ cw-vs-balanced-ots.png")


if __name__ == "__main__":
    main()
