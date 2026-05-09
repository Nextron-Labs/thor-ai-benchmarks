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



def pareto_min_min(rows, x_key, y_key):
    frontier = []
    for m in rows:
        dominated = False
        for o in rows:
            if o is m:
                continue
            if (o[x_key] <= m[x_key] and o[y_key] <= m[y_key] and
                    (o[x_key] < m[x_key] or o[y_key] < m[y_key])):
                dominated = True
                break
        if not dominated:
            frontier.append(m["model"])
    return set(frontier)


def pareto_min_max(rows, x_key, y_key):
    frontier = []
    for m in rows:
        dominated = False
        for o in rows:
            if o is m:
                continue
            if (o[x_key] <= m[x_key] and o[y_key] >= m[y_key] and
                    (o[x_key] < m[x_key] or o[y_key] > m[y_key])):
                dominated = True
                break
        if not dominated:
            frontier.append(m["model"])
    return set(frontier)


def pareto_max_max(rows, x_key, y_key):
    frontier = []
    for m in rows:
        dominated = False
        for o in rows:
            if o is m:
                continue
            if (o[x_key] >= m[x_key] and o[y_key] >= m[y_key] and
                    (o[x_key] > m[x_key] or o[y_key] > m[y_key])):
                dominated = True
                break
        if not dominated:
            frontier.append(m["model"])
    return set(frontier)


def add_corner_labels(ax, upper_left, upper_right, lower_left, lower_right):
    box = dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor="lightgray", alpha=0.86)
    ax.text(0.02, 0.97, upper_left, transform=ax.transAxes, ha="left", va="top", fontsize=8.5, bbox=box)
    ax.text(0.98, 0.97, upper_right, transform=ax.transAxes, ha="right", va="top", fontsize=8.5, bbox=box)
    ax.text(0.02, 0.03, lower_left, transform=ax.transAxes, ha="left", va="bottom", fontsize=8.5, bbox=box)
    ax.text(0.98, 0.03, lower_right, transform=ax.transAxes, ha="right", va="bottom", fontsize=8.5, bbox=box)


def label_points(ax, rows, x_key, y_key, labels, all_labels=False):
    """Deterministic label placement. adjustText is optional and not required."""
    labels = set(labels)
    offsets = [(7, 5), (7, -10), (-7, 5), (-7, -10), (10, 12), (-10, 12), (10, -16), (-10, -16)]
    texts = []
    for i, m in enumerate(rows):
        if all_labels or m["model"] in labels:
            dx, dy = offsets[i % len(offsets)]
            ha = "left" if dx > 0 else "right"
            t = ax.annotate(
                m["model"],
                (m[x_key], m[y_key]),
                xytext=(dx, dy),
                textcoords="offset points",
                fontsize=7.5 if all_labels else 8.5,
                ha=ha,
                va="center",
                bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none", alpha=0.72),
                arrowprops=dict(arrowstyle="-", color="gray", lw=0.35, alpha=0.55) if not all_labels else None,
                zorder=10,
            )
            texts.append(t)
    try:
        from adjustText import adjust_text
        adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle="-", color="gray", lw=0.4, alpha=0.55))
    except Exception:
        pass


def scatter_charts(models, baselines):
    profile_leaders = {"llama-3.1-8b", "deepseek-v3.2", "deepseek-v4-flash"}
    mentioned = profile_leaders | {"gpt-5-nano", "nemotron-3-nano-omni", "llama-3.1-70b", "qwen3-235b-a22b", "minimax-m2.5", "gpt-oss-120b", "gemma4-31b", "grok-4.20"}
    all_rows = models + baselines
    baseline_names = {m["model"] for m in baselines}

    def draw_scatter(filename, x_key, y_key, color_key, size_key, title, xlabel, ylabel,
                     pareto_names, top_names, corner_labels, color_label, cmap="RdYlGn_r", all_labels=False):
        fig, ax = plt.subplots(figsize=(13.5, 9))
        normal = [m for m in all_rows if m["tier"] != "baseline"]
        base = [m for m in all_rows if m["tier"] == "baseline"]
        sizes = [90 + max(float(m.get(size_key, 0)), 0) * 3 for m in normal]
        sc = ax.scatter(
            [m[x_key] for m in normal], [m[y_key] for m in normal],
            c=[m[color_key] for m in normal], cmap=cmap, s=sizes,
            alpha=0.72, edgecolors="gray", linewidths=0.6, zorder=3,
        )
        ax.scatter(
            [m[x_key] for m in base], [m[y_key] for m in base],
            marker="X", s=210, c="#111111", edgecolors="white", linewidths=0.9,
            label="Baselines", zorder=6,
        )
        frontier = [m for m in all_rows if m["model"] in pareto_names]
        ax.scatter(
            [m[x_key] for m in frontier], [m[y_key] for m in frontier],
            facecolors="none", edgecolors="#f1c40f", linewidths=2.1, s=250,
            label="Pareto frontier", zorder=7,
        )
        # Add plot padding before labels/corner notes so baselines at 0/100 do not
        # collide with the explanatory corner boxes.
        xs = [m[x_key] for m in all_rows]
        ys = [m[y_key] for m in all_rows]
        x_span = max(xs) - min(xs) or 1
        y_span = max(ys) - min(ys) or 1
        ax.set_xlim(min(xs) - x_span * 0.10, max(xs) + x_span * 0.10)
        ax.set_ylim(min(ys) - y_span * 0.12, max(ys) + y_span * 0.12)

        label_set = profile_leaders | mentioned | baseline_names | pareto_names | set(top_names)
        label_points(ax, all_rows, x_key, y_key, label_set, all_labels=all_labels)
        add_corner_labels(ax, *corner_labels)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(alpha=0.25)
        ax.legend(loc="best", framealpha=0.9)
        cbar = fig.colorbar(sc, ax=ax)
        cbar.set_label(color_label)
        plt.tight_layout()
        fig.savefig(CHARTS / filename, dpi=150)

    # 1. Critical Miss Rate vs False Review Load: lower/lower is better.
    cm_pareto = pareto_min_min(all_rows, "false_review", "critical_miss")
    cm_top = {m["model"] for m in sorted(models, key=lambda m: (m["critical_miss"], m["false_review"]))[:10]}
    for suffix, all_labels in [("", False), ("-full-labeled", True)]:
        draw_scatter(
            f"critical-miss-vs-false-review{suffix}.png",
            "false_review", "critical_miss", "balanced_ots", "balanced_ots",
            "Critical Miss Rate vs False Review Load",
            "False Review Load (%) — lower is less analyst review",
            "Critical Miss Rate (%) — lower is safer",
            cm_pareto, cm_top,
            (
                "Upper-left\nefficient but risky",
                "Upper-right\nworst: noisy + risky",
                "Lower-left\nideal: safe + efficient",
                "Lower-right\nsafe but noisy",
            ),
            "Balanced OTS (%)", cmap="viridis", all_labels=all_labels,
        )

    # 2. Balanced OTS vs False Review Load: lower x / higher y is better.
    bo_pareto = pareto_min_max(all_rows, "false_review", "balanced_ots")
    bo_top = {m["model"] for m in sorted(models, key=lambda m: m["balanced_ots"], reverse=True)[:10]}
    for suffix, all_labels in [("", False), ("-full-labeled", True)]:
        draw_scatter(
            f"balanced-ots-vs-false-review{suffix}.png",
            "false_review", "balanced_ots", "critical_miss", "balanced_ots",
            "Balanced OTS vs False Review Load",
            "False Review Load (%) — lower is better",
            "Balanced OTS (%) — higher is better",
            bo_pareto, bo_top,
            (
                "Upper-left\nbest trade-off",
                "Upper-right\nstrong but noisy",
                "Lower-left\nefficient but weak",
                "Lower-right\nweak and noisy",
            ),
            "Critical Miss Rate (%)", cmap="RdYlGn_r", all_labels=all_labels,
        )

    # 3. CW% vs Balanced OTS: higher/higher is better.
    cw_pareto = pareto_max_max(all_rows, "cw_pct", "balanced_ots")
    cw_top = {m["model"] for m in sorted(models, key=lambda m: m["cw_pct"], reverse=True)[:10]}
    for suffix, all_labels in [("", False), ("-full-labeled", True)]:
        draw_scatter(
            f"cw-vs-balanced-ots{suffix}.png",
            "cw_pct", "balanced_ots", "critical_miss", "balanced_ots",
            "CW% vs Balanced OTS",
            "CW% — higher is better",
            "Balanced OTS (%) — higher is better",
            cw_pareto, cw_top,
            (
                "Upper-left\noperationally useful,\nlower classic score",
                "Upper-right\nstrong on both views",
                "Lower-left\nweak on both views",
                "Lower-right\nhigh CW%, weaker ops",
            ),
            "Critical Miss Rate (%)", cmap="RdYlGn_r", all_labels=all_labels,
        )

def main():
    rows = load_rows()
    baselines = [r for r in rows if r["tier"] == "baseline"]
    models = [r for r in rows if r["tier"] != "baseline"]
    profile_rows = write_profile_csvs(models)
    write_baseline_csv(baselines)
    plot_profile_summary(profile_rows, baselines)
    scatter_charts(models, baselines)
    print("✓ operational profile CSVs")
    print("✓ operational-profile-summary.png")
    print("✓ critical-miss-vs-false-review.png")
    print("✓ balanced-ots-vs-false-review.png")
    print("✓ cw-vs-balanced-ots.png")
    print("✓ full-labeled scatter appendix charts")


if __name__ == "__main__":
    main()
