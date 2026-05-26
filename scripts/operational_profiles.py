#!/usr/bin/env python3
"""Generate operational profile CSVs and charts for THOR AI Benchmarks."""

import csv
import json
import re
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from openrouter_costs import estimate_run_cost_cents, load_pricing_snapshot

ROOT = Path(__file__).resolve().parent.parent
COMBINED = ROOT / "combined"
CHARTS = ROOT / "charts"
CHARTS.mkdir(exist_ok=True)
TIERS_PATH = ROOT / "scripts" / "model_tiers.json"

TIER_SLUGS = {
    "closed_source": "closed-source",
    "open_source_pro": "open-source-pro",
    "open_source_consumer": "open-source-consumer",
}

PROFILE_SLUGS = {
    "High-safety": "high-safety",
    "Balanced SOC": "balanced-soc",
    "Noise-reduction": "noise-reduction",
}

PROFILE_USE_CASES = {
    "High-safety": "High-safety triage",
    "Balanced SOC": "Balanced SOC triage",
    "Noise-reduction": "Noise reduction / high-volume triage",
}

PROFILE_DESCRIPTIONS = {
    "High-safety": "Critical Miss ≤ 5%, Threat Capture ≥ 95%, False Review ≤ 75%; ranked by Balanced OTS, then False Review Load.",
    "Balanced SOC": "Critical Miss ≤ 15%, Threat Capture ≥ 85%, False Review ≤ 75%; ranked by Balanced OTS.",
    "Noise-reduction": "False Review ≤ 55%, Critical Miss ≤ 20%, Balanced OTS > 0; ranked by False Review Load, then Balanced OTS.",
}

PROFILES = [
    {
        "name": "High-safety",
        "csv": "operational-profile-high-safety.csv",
        # Recommendation guardrail: a high-safety model must still reduce review
        # load meaningfully. Anything close to always-inc belongs in analysis, not
        # in the recommended profile table.
        "requirements": lambda m: m["critical_miss"] <= 5 and m["threat_capture"] >= 95 and m["false_review"] <= 75,
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
INTS = {"exact", "minor", "hard", "hard_miss", "hard_over", "n_errors", "n", "total_tokens"}

GENERATED_SUMMARY_START = "<!-- BEGIN GENERATED:CURRENT_RESULT_SUMMARY -->"
GENERATED_SUMMARY_END = "<!-- END GENERATED:CURRENT_RESULT_SUMMARY -->"
GENERATED_CHART_NARRATIVE_START = "<!-- BEGIN GENERATED:CHART_NARRATIVE -->"
GENERATED_CHART_NARRATIVE_END = "<!-- END GENERATED:CHART_NARRATIVE -->"
GENERATED_FULL_DATA_START = "<!-- BEGIN GENERATED:FULL_DATA -->"
GENERATED_FULL_DATA_END = "<!-- END GENERATED:FULL_DATA -->"


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


def load_tiers():
    with open(TIERS_PATH) as f:
        cfg = json.load(f)
    tiers = cfg["tiers"]
    tier_lookup = {}
    for tier_key, tier_data in tiers.items():
        for model in tier_data["models"]:
            tier_lookup[model] = tier_key
    return tiers, tier_lookup


def resolve_tier(model, tiers, tier_lookup):
    row_tier = model.get("tier")
    if row_tier in tiers:
        return row_tier
    fallback_tier = tier_lookup.get(model["model"])
    if fallback_tier in tiers:
        return fallback_tier
    raise KeyError(model["model"])


def validate_tiers(models, tiers, tier_lookup):
    missing = []
    for model in models:
        try:
            model["tier"] = resolve_tier(model, tiers, tier_lookup)
        except KeyError:
            missing.append(model["model"])
    if missing:
        raise SystemExit(
            "Models without a known tier in combined/leaderboard data or scripts/model_tiers.json: "
            + ", ".join(sorted(missing))
        )


def fmt_metric(value, suffix="%"):
    if value in (None, "", "–", "-"):
        return "—"
    return f"{float(value):.1f}{suffix}"


def fmt_cost(cents):
    if cents in (None, "", "–", "-"):
        return "—"
    return f"${float(cents) / 100:.2f}"


def attach_estimated_costs(rows):
    pricing_snapshot = load_pricing_snapshot()
    for row in rows:
        row["estimated_run_cost_cents"] = estimate_run_cost_cents(
            row["model"], row.get("total_tokens"), pricing_snapshot
        )


def csv_cost(row):
    cents = row.get("estimated_run_cost_cents")
    if cents in (None, "", "–", "-"):
        return ""
    return f"{float(cents) / 100:.2f}"


def replace_generated_block(text, start_marker, end_marker, replacement, fallback_start=None, fallback_end=None):
    wrapped = f"{start_marker}\n{replacement.rstrip()}\n{end_marker}"
    if start_marker in text and end_marker in text:
        start = text.index(start_marker)
        end = text.index(end_marker) + len(end_marker)
        return text[:start] + wrapped + text[end:]

    if fallback_start is None or fallback_end is None:
        raise SystemExit(f"Missing generated block markers: {start_marker} / {end_marker}")

    start = text.index(fallback_start)
    end = text.index(fallback_end)
    prefix = text[:start].rstrip()
    suffix = text[end:].lstrip()
    return prefix + "\n\n" + wrapped + "\n\n" + suffix


def current_result_dimensions(models):
    finding_count = max((int(m.get("n", 0)) for m in models), default=0)
    report_set = ""
    results_path = COMBINED / "results-combined.json"
    if results_path.exists():
        with open(results_path) as f:
            results = json.load(f)
        combined_keys = [key for key in results if "+" in key.split("/")[-1]]
        if combined_keys:
            report_set = max(
                (key.split("/")[-1] for key in combined_keys),
                key=lambda value: (value.count("+") + 1, value),
            )
            finding_count = max(
                (
                    score.get("n_expected", score.get("n_matched", finding_count))
                    for key, score in results.items()
                    if key.endswith("/" + report_set)
                ),
                default=finding_count,
            )
    report_count = report_set.count("+") + 1 if report_set else 0
    if report_set:
        def report_number(label):
            match = re.search(r"\d+", label)
            return int(match.group(0)) if match else 0

        parts = sorted(report_set.split("+"), key=report_number)
        report_range = f"{parts[0]}-{parts[-1]}" if len(parts) > 1 else parts[0]
    else:
        report_range = "current report set"
    return report_count, finding_count, report_set, report_range


def render_dropped_models_section():
    dropped_path = COMBINED / "dropped-models.json"
    dropped = []
    if dropped_path.exists():
        with open(dropped_path) as f:
            dropped = json.load(f)

    lines = [
        "## Incomplete / Dropped Model Attempts",
        "",
        "Public benchmark charts and leaderboards include complete model runs only. If a model repeatedly fails to return valid structured results for every scored finding, we drop it from the public benchmark instead of ranking a partial result. Current dropped attempts are listed in `combined/dropped-models.json`:",
        "",
    ]
    if dropped:
        for item in sorted(dropped, key=lambda row: row.get("model", "")):
            lines.append(f"- `{item.get('model')}` — {item.get('reason', 'dropped from public artifacts')}")
    else:
        lines.append("There are currently no dropped model attempts.")
    lines.append("")
    return "\n".join(lines)


def update_static_readme_counts(text, models):
    report_count, finding_count, _report_set, report_range = current_result_dimensions(models)
    model_count = len([m for m in models if not m.get("incomplete")])
    text = re.sub(
        r"The current public result set covers \*\*[^*]+ complete models\*\*, \*\*[^*]+ THOR reports\*\*, and \*\*[^*]+ expert-classified findings\*\*\.",
        f"The current public result set covers **{model_count} complete models**, **{report_count} THOR reports**, and **{finding_count} expert-classified findings**.",
        text,
        count=1,
    )
    text = re.sub(r"current full R1[–-]R9 finding set", f"current full {report_range} finding set", text)
    text = re.sub(r"current full R1[–-]R9 report set", f"current full {report_range} report set", text)
    text = re.sub(
        r"## Incomplete / Dropped Model Attempts\n.*?\n(?=## What We Benchmark)",
        render_dropped_models_section() + "\n",
        text,
        flags=re.S,
    )
    return text


def closest_candidate(models, profile):
    complete = [m for m in models if not m["incomplete"]]
    if not complete:
        return None, "no complete models in this tier"

    def violations(m):
        reasons = []
        if profile["name"] == "High-safety":
            if m["critical_miss"] > 5:
                reasons.append(f"Critical Miss {m['critical_miss']:.1f}% > 5%")
            if m["threat_capture"] < 95:
                reasons.append(f"Threat Capture {m['threat_capture']:.1f}% < 95%")
            if m["false_review"] > 75:
                reasons.append(f"False Review {m['false_review']:.1f}% > 75%")
        elif profile["name"] == "Balanced SOC":
            if m["critical_miss"] > 15:
                reasons.append(f"Critical Miss {m['critical_miss']:.1f}% > 15%")
            if m["threat_capture"] < 85:
                reasons.append(f"Threat Capture {m['threat_capture']:.1f}% < 85%")
            if m["false_review"] > 75:
                reasons.append(f"False Review {m['false_review']:.1f}% > 75%")
        else:
            if m["false_review"] > 55:
                reasons.append(f"False Review {m['false_review']:.1f}% > 55%")
            if m["critical_miss"] > 20:
                reasons.append(f"Critical Miss {m['critical_miss']:.1f}% > 20%")
            if m["balanced_ots"] <= 0:
                reasons.append(f"Balanced OTS {m['balanced_ots']:.1f}% ≤ 0")
        return reasons

    # Prefer the same profile ranking and then the fewest/smallest guardrail misses.
    ranked = sorted(complete, key=profile["sort"])
    ranked.sort(key=lambda m: (len(violations(m)), profile["sort"](m)))
    candidate = ranked[0]
    return candidate, "; ".join(violations(candidate)) or "closest by profile ranking"


def why_for_leader(row, profile_name, tier_rows, scope="tier"):
    notes = []
    if profile_name == "Noise-reduction":
        notes.append(f"Lowest False Review Load {'overall' if scope == 'overall' else 'in this tier'} among models that cleared the guardrails")
    else:
        notes.append("Profile leader under current constraints by Balanced OTS")
    if row["critical_miss"] == 0:
        notes.append("0.0% Critical Miss")
    elif profile_name == "High-safety" and row["critical_miss"] >= 4:
        notes.append("Critical Miss Rate is close to the 5% threshold")
    elif profile_name == "Balanced SOC" and row["critical_miss"] >= 12:
        notes.append("Critical Miss Rate is close to the 15% threshold")
    elif profile_name == "Noise-reduction" and row["critical_miss"] >= 16:
        notes.append("Critical Miss Rate is close to the 20% threshold")
    if row["false_review"] >= 60:
        notes.append("high review load")
    elif row["false_review"] <= 30:
        notes.append("low review load")
    if row.get("avg_seconds_per_event", 0) and row["avg_seconds_per_event"] >= 50:
        notes.append("slower than many candidates")
    if len(tier_rows) == 1:
        notes.append("only model in this tier that cleared the guardrails")
    return "; ".join(notes) + "."


def write_profile_csvs(models):
    profile_rows = {}
    fields = ["rank", "model", "cw_pct", "balanced_ots", "critical_miss", "threat_capture", "false_review", "false_escalation", "cost_per_run", "avg_seconds_per_event", "n", "incomplete"]
    for profile in PROFILES:
        matched = [m for m in models if not m["incomplete"] and profile["requirements"](m)]
        matched.sort(key=profile["sort"])
        profile_rows[profile["name"]] = matched
        with open(COMBINED / profile["csv"], "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
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
                    "cost_per_run": csv_cost(m),
                    "avg_seconds_per_event": f"{m.get('avg_seconds_per_event', 0):.2f}",
                    "n": m["n"],
                    "incomplete": m["incomplete"],
                })
    return profile_rows


def write_tier_profile_csvs(models, tiers):
    fields = ["rank", "model", "cw_pct", "balanced_ots", "critical_miss", "threat_capture", "false_review", "false_escalation", "cost_per_run", "avg_seconds_per_event", "n", "incomplete"]
    tier_profile_rows = {}
    for tier_key in tiers:
        tier_models = [m for m in models if m["tier"] == tier_key]
        tier_profile_rows[tier_key] = {}
        for profile in PROFILES:
            matched = [m for m in tier_models if not m["incomplete"] and profile["requirements"](m)]
            matched.sort(key=profile["sort"])
            tier_profile_rows[tier_key][profile["name"]] = matched
            filename = f"operational-profile-{PROFILE_SLUGS[profile['name']]}-{TIER_SLUGS[tier_key]}.csv"
            with open(COMBINED / filename, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
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
                        "cost_per_run": csv_cost(m),
                        "avg_seconds_per_event": f"{m.get('avg_seconds_per_event', 0):.2f}",
                        "n": m["n"],
                        "incomplete": m["incomplete"],
                    })
    return tier_profile_rows


def write_tier_summary_csv(models, tiers, tier_profile_rows):
    fields = [
        "tier", "profile", "recommended_model", "cw_pct", "balanced_ots", "critical_miss_rate",
        "threat_capture_rate", "false_review_load", "false_escalation_rate", "cost_per_run",
        "avg_seconds_per_event", "recommendation_status", "exclusion_reason_if_none",
    ]
    rows = []
    for tier_key, tier_data in tiers.items():
        tier_models = [m for m in models if m["tier"] == tier_key]
        for profile in PROFILES:
            matched = tier_profile_rows[tier_key][profile["name"]]
            if matched:
                m = matched[0]
                rows.append({
                    "tier": tier_data["label"],
                    "profile": profile["name"],
                    "recommended_model": m["model"],
                    "cw_pct": f"{m['cw_pct']:.1f}",
                    "balanced_ots": f"{m['balanced_ots']:.1f}",
                    "critical_miss_rate": f"{m['critical_miss']:.1f}",
                    "threat_capture_rate": f"{m['threat_capture']:.1f}",
                    "false_review_load": f"{m['false_review']:.1f}",
                    "false_escalation_rate": f"{m['false_escalation']:.1f}",
                    "cost_per_run": fmt_cost(m.get("estimated_run_cost_cents")),
                    "avg_seconds_per_event": f"{m.get('avg_seconds_per_event', 0):.2f}",
                    "recommendation_status": "profile leader under current constraints",
                    "exclusion_reason_if_none": "",
                })
            else:
                closest, reason = closest_candidate(tier_models, profile)
                closest_note = f"Closest candidate: {closest['model']}, but it failed because {reason}." if closest else reason
                rows.append({
                    "tier": tier_data["label"],
                    "profile": profile["name"],
                    "recommended_model": "",
                    "cw_pct": "", "balanced_ots": "", "critical_miss_rate": "", "threat_capture_rate": "",
                    "false_review_load": "", "false_escalation_rate": "", "cost_per_run": "", "avg_seconds_per_event": "",
                    "recommendation_status": "no model cleared the current guardrails",
                    "exclusion_reason_if_none": closest_note,
                })
    with open(COMBINED / "operational-profile-summary-by-tier.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return rows


def write_baseline_csv(baselines):
    fields = ["strategy", "cw_pct", "balanced_ots", "critical_miss", "threat_capture", "false_review", "false_escalation", "cost_per_run"]
    with open(COMBINED / "operational-baselines.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
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
    b1 = ax.bar(x - width, [p["balanced_ots"] for p in points], width, label="Balanced OTS", color="#3498db")
    b2 = ax.bar(x, [p["critical_miss"] for p in points], width, label="Critical Miss Rate", color="#e74c3c")
    b3 = ax.bar(x + width, [p["false_review"] for p in points], width, label="False Review Load", color="#95a5a6")
    for bars in (b1, b2, b3):
        for bar in bars:
            val = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                val + 1.4,
                f"{val:.1f}%",
                ha="center",
                va="bottom",
                fontsize=8,
                rotation=90,
            )
    for i, p in enumerate(points):
        ax.text(i, 108, p["model"].replace("always-", "always-\n"), ha="center", va="top", fontsize=9, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 116)
    ax.set_ylabel("Percent")
    ax.set_title("Operational Profile Leaders vs always-inc Safety Baseline")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=3, framealpha=0.9)
    ax.grid(axis="y", alpha=0.25)
    plt.tight_layout()
    fig.savefig(CHARTS / "operational-profile-summary.png", dpi=150)


def plot_tier_profile_summary(tiers, tier_profile_rows):
    profiles = [p["name"] for p in PROFILES]
    tier_keys = list(tiers.keys())
    fig, ax = plt.subplots(figsize=(14, 6.5))
    ax.set_xlim(0, len(profiles))
    ax.set_ylim(0, len(tier_keys))
    ax.set_xticks(np.arange(len(profiles)) + 0.5)
    ax.set_xticklabels([PROFILE_USE_CASES[p].replace(" / ", " /\n") for p in profiles], fontsize=10)
    ax.set_yticks(np.arange(len(tier_keys)) + 0.5)
    ax.set_yticklabels([tiers[t]["label"].replace(" (", "\n(") for t in tier_keys], fontsize=10)
    ax.invert_yaxis()

    for y, tier_key in enumerate(tier_keys):
        color = tiers[tier_key]["color"]
        for x, profile_name in enumerate(profiles):
            rows = tier_profile_rows[tier_key][profile_name]
            rect = plt.Rectangle((x, y), 1, 1, facecolor=color, alpha=0.18, edgecolor="white", linewidth=2)
            ax.add_patch(rect)
            if rows:
                m = rows[0]
                text = (
                    f"{m['model']}\n"
                    f"BalOTS {m['balanced_ots']:.1f}%\n"
                    f"CritMiss {m['critical_miss']:.1f}% · FalseRev {m['false_review']:.1f}%"
                )
                weight = "bold"
            else:
                text = "No model cleared\ncurrent guardrails"
                weight = "normal"
            ax.text(x + 0.5, y + 0.5, text, ha="center", va="center", fontsize=9, fontweight=weight, wrap=True)

    ax.set_title("Operational Profile Leaders by Model Tier", fontsize=14, fontweight="bold")
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.text(
        0.5, -0.18,
        "Cells show profile leaders under the same guardrails as the global tables. Empty cells mean no model in that tier cleared the guardrails.",
        transform=ax.transAxes, ha="center", va="top", fontsize=9,
    )
    plt.tight_layout()
    fig.savefig(CHARTS / "operational-profile-summary-by-tier.png", dpi=150, bbox_inches="tight")



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
    """Deterministic label placement with adjustText for leader lines."""
    labels = set(labels)
    texts = []
    target_x = []
    target_y = []
    for i, m in enumerate(rows):
        if all_labels or m["model"] in labels:
            # Create text positioned near the point
            t = ax.text(
                m[x_key], m[y_key],
                m["model"],
                fontsize=7.5 if all_labels else 8.5,
                ha="left",
                va="center",
                bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none", alpha=0.72),
                zorder=10,
            )
            texts.append(t)
            target_x.append(m[x_key])
            target_y.append(m[y_key])
    try:
        from adjustText import adjust_text
        # Pass target positions so arrows point to actual data points
        adjust_text(texts, ax=ax, target_x=target_x, target_y=target_y,
                    min_arrow_len=2.0,
            arrowprops=dict(arrowstyle="-", color="gray", lw=0.4, alpha=0.55))
    except Exception:
        # Fallback: no leader lines if adjustText not available
        pass


def scatter_charts(models, baselines, tiers):
    profile_leaders = set()
    profile_top_models = set()
    for profile in PROFILES:
        matched = [m for m in models if not m["incomplete"] and profile["requirements"](m)]
        matched.sort(key=profile["sort"])
        if matched:
            profile_leaders.add(matched[0]["model"])
            profile_top_models.update(m["model"] for m in matched[:5])

    # Keep labels aligned with the generated profile tables instead of freezing
    # old README leaders into the charts.
    mentioned = profile_leaders | profile_top_models | {"llama-3.1-8b", "deepseek-v3.2", "deepseek-v4-flash"}
    all_rows = models + baselines
    baseline_names = {m["model"] for m in baselines}

    def draw_scatter(filename, x_key, y_key, color_key, size_key, title, xlabel, ylabel,
                     pareto_names, top_names, corner_labels, color_label, cmap="RdYlGn_r", all_labels=False):
        fig, ax = plt.subplots(figsize=(13.5, 9))
        normal = [m for m in all_rows if m["tier"] != "baseline"]
        base = [m for m in all_rows if m["tier"] == "baseline"]
        color_values = [m[color_key] for m in normal]
        vmin = min(color_values) if color_values else 0
        vmax = max(color_values) if color_values else 1
        sc = None
        for tier_key, tier_data in tiers.items():
            tier_rows = [m for m in normal if m["tier"] == tier_key]
            if not tier_rows:
                continue
            sizes = [90 + max(float(m.get(size_key, 0)), 0) * 3 for m in tier_rows]
            sc = ax.scatter(
                [m[x_key] for m in tier_rows], [m[y_key] for m in tier_rows],
                c=[m[color_key] for m in tier_rows], cmap=cmap, vmin=vmin, vmax=vmax, s=sizes,
                marker=tier_data["marker"], alpha=0.72, edgecolors="gray", linewidths=0.6,
                label=tier_data["label"], zorder=3,
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
        if sc is not None:
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


def markdown_global_table(profile_rows):
    lines = ["| Use case | Suggested model | Why |", "|---|---|---|"]
    for profile in PROFILES:
        rows = profile_rows[profile["name"]]
        if rows:
            m = rows[0]
            why = why_for_leader(m, profile["name"], rows, scope="overall")
            lines.append(f"| {PROFILE_USE_CASES[profile['name']]} | `{m['model']}` | {why} |")
        else:
            lines.append(f"| {PROFILE_USE_CASES[profile['name']]} | No model cleared the current guardrails | {PROFILE_DESCRIPTIONS[profile['name']]} |")
    return "\n".join(lines)


def markdown_tier_tables(models, tiers, tier_profile_rows):
    lines = [
        "## Current Result Summary by Model Tier",
        "",
        "Deployment constraints matter. A vendor API model may be easy to test, but some users need local execution, open-source weights, predictable cost, or consumer-hardware feasibility. The following tables show the current profile leaders within each model tier.",
        "",
    ]
    for tier_key, tier_data in tiers.items():
        title = tier_data["label"].replace("(", "/ ").replace(")", "")
        title = title.replace("Closed Source / Vendor API", "Closed Source / Vendor API")
        title = title.replace("Open Source / Pro Hardware", "Open Source / Pro Hardware")
        title = title.replace("Open Source / Consumer Hardware <10k", "Open Source / Consumer Hardware")
        lines.extend([f"### {title}", "", "| Use case | Suggested model | Why |", "|---|---|---|"])
        tier_models = [m for m in models if m["tier"] == tier_key]
        for profile in PROFILES:
            rows = tier_profile_rows[tier_key][profile["name"]]
            if rows:
                m = rows[0]
                lines.append(f"| {PROFILE_USE_CASES[profile['name']]} | `{m['model']}` | {why_for_leader(m, profile['name'], rows)} |")
            else:
                closest, reason = closest_candidate(tier_models, profile)
                if closest:
                    why = f"Closest candidate: `{closest['model']}`, but it failed because {reason}."
                else:
                    why = reason
                lines.append(f"| {PROFILE_USE_CASES[profile['name']]} | No model cleared the current guardrails | {why} |")
        lines.append("")

    lines.extend([
        "### Why model tiers matter",
        "",
        "Model tier matters because deployment constraints are part of the decision. A vendor API model may score well, but it may not be usable in environments that require local processing, predictable fixed cost, or strict data-control boundaries. Open-source models on pro hardware can be attractive for controlled deployments. Consumer-hardware models are relevant when the goal is local triage with lower infrastructure cost, even if quality may be lower.",
        "",
    ])
    return "\n".join(lines).rstrip()


PROFILE_README_DETAILS = {
    "High-safety": {
        "heading": "High-Safety",
        "use_case": "Environments where missing a real incident is unacceptable or very costly, such as critical infrastructure, high-value targets, or highly regulated environments.",
        "requirements": "Complete coverage across the benchmark set; Critical Miss Rate ≤ 5%; Threat Capture Rate ≥ 95%; False Review Load ≤ 75%.",
        "ranking": "Balanced OTS descending, then False Review Load ascending.",
    },
    "Balanced SOC": {
        "heading": "Balanced SOC",
        "use_case": "General SOC operations where both safety and analyst workload matter.",
        "requirements": "Complete coverage across the benchmark set; Critical Miss Rate ≤ 15%; Threat Capture Rate ≥ 85%; False Review Load ≤ 75%.",
        "ranking": "Balanced OTS descending.",
    },
    "Noise-reduction": {
        "heading": "Noise-Reduction / High-Volume Triage",
        "use_case": "High-volume alert or finding triage where reducing analyst review load is a priority and some miss risk is accepted.",
        "requirements": "Complete coverage across the benchmark set; False Review Load ≤ 55%; Critical Miss Rate ≤ 20%; Balanced OTS > 0.",
        "ranking": "False Review Load ascending, then Balanced OTS descending.",
    },
}


def render_operational_profiles_section(models, profile_rows):
    lines = ["## Operational Profiles", ""]
    complete_count = len([m for m in models if not m.get("incomplete")])
    for profile in PROFILES:
        name = profile["name"]
        details = PROFILE_README_DETAILS[name]
        rows = profile_rows.get(name, [])
        lines.extend([
            f"### {details['heading']}",
            "",
            f"**Use case:** {details['use_case']}",
            "",
            f"**Requirements:** {details['requirements']}",
            "",
            f"**Ranking rule:** {details['ranking']}",
            "",
            "| # | Model | CW% | BalOTS | CritMiss | ThreatCap | FalseRev | FalseEsc | Cost/Run | AvgTime |",
            "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ])
        for idx, row in enumerate(rows[:10], 1):
            lines.append(
                f"| {idx} | `{row['model']}` | {row['cw_pct']:.1f}% | {row['balanced_ots']:.1f}% | "
                f"{row['critical_miss']:.1f}% | {row['threat_capture']:.1f}% | {row['false_review']:.1f}% | "
                f"{row['false_escalation']:.1f}% | {fmt_cost(row.get('estimated_run_cost_cents'))} | "
                f"{row.get('avg_seconds_per_event', 0):.2f}s |"
            )
        if not rows:
            lines.append("| — | No model cleared the current guardrails | — | — | — | — | — | — | — | — |")
        lines.extend([
            "",
            f"**Shown:** top {min(10, len(rows))} / {len(rows)} matched models. **Matched:** {len(rows)} / {complete_count} complete models.",
            "",
        ])
        if rows:
            lines.append(
                f"**Interpretation:** Under these constraints, `{rows[0]['model']}` is the current profile leader. "
                f"Values in this section are generated from `combined/{profile['csv']}`."
            )
        else:
            lines.append(
                f"**Interpretation:** No complete model currently clears these constraints. "
                f"Values in this section are generated from `combined/{profile['csv']}`."
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def generate_chart_narrative(profile_rows, tier_profile_rows):
    """Generate narrative text for chart descriptions based on current profile leaders."""
    # Get overall leaders for each profile
    high_safety = profile_rows.get("High-safety", [])
    balanced_soc = profile_rows.get("Balanced SOC", [])
    noise_reduction = profile_rows.get("Noise-reduction", [])
    
    lines = []
    
    # Build dynamic narrative for overall leaders
    hs_model = high_safety[0]["model"] if high_safety else None
    bs_model = balanced_soc[0]["model"] if balanced_soc else None
    nr_model = noise_reduction[0]["model"] if noise_reduction else None
    
    hs_cm = high_safety[0].get("critical_miss", 0) if high_safety else None
    nr_cm = noise_reduction[0].get("critical_miss", 0) if noise_reduction else None
    
    if hs_model and hs_model == bs_model:
        lines.append(f"`{hs_model}` is now both the high-safety and balanced SOC profile leader under the current constraints.")
    else:
        if hs_model:
            lines.append(f"`{hs_model}` is the high-safety profile leader.")
        if bs_model:
            lines.append(f"`{bs_model}` is the balanced SOC profile leader.")
    
    if nr_model:
        if nr_model == hs_model:
            lines.append(f"It also reduces review load under the noise-reduction profile.")
        else:
            nr_note = f"`{nr_model}` reduces review load the most under the noise-reduction profile"
            if nr_cm and nr_cm > 5:
                nr_note += f", but has higher miss risk ({nr_cm:.1f}% Critical Miss) than the high-safety leader"
            nr_note += "."
            lines.append(nr_note)
    
    lines.append("`always-inc` is a safety reference, not a useful triage model.")
    
    return "\n".join(lines)


def update_readme(models, tiers, profile_rows, tier_profile_rows):
    readme = ROOT / "README.md"
    text = update_static_readme_counts(readme.read_text(), models)
    section = f"""## Current Result Summary - Overall

The first table ignores deployment tier and shows the current profile leaders across all tested models. These are **current profile leaders under the selected constraints**, not universal winners. A model only appears as a recommendation if it also clears minimum usefulness and completeness guardrails; near-`always-inc` behavior is analysis material, not a benchmark recommendation.

{markdown_global_table(profile_rows)}

There is no single best model. The useful choice depends on whether the deployment optimizes for missed-incident avoidance, balanced SOC triage, review-load reduction, cost, latency, data-control boundaries, or hardware constraints. The global winner is not automatically the best option for local or open-source deployments.

{markdown_tier_tables(models, tiers, tier_profile_rows)}

"""
    text = replace_generated_block(
        text,
        GENERATED_SUMMARY_START,
        GENERATED_SUMMARY_END,
        section,
        fallback_start="## Current Result Summary",
        fallback_end="## Reader Guide",
    )

    full_section = """## Full Data

Sortable and machine-readable data:

- [combined/leaderboard.csv](combined/leaderboard.csv)
- [combined/leaderboard.json](combined/leaderboard.json)
- [combined/operational-baselines.csv](combined/operational-baselines.csv)
- [combined/operational-profile-high-safety.csv](combined/operational-profile-high-safety.csv)
- [combined/operational-profile-balanced-soc.csv](combined/operational-profile-balanced-soc.csv)
- [combined/operational-profile-noise-reduction.csv](combined/operational-profile-noise-reduction.csv)
- [combined/operational-profile-summary-by-tier.csv](combined/operational-profile-summary-by-tier.csv)

Tier-specific operational profile CSVs:

- [combined/operational-profile-high-safety-closed-source.csv](combined/operational-profile-high-safety-closed-source.csv)
- [combined/operational-profile-balanced-soc-closed-source.csv](combined/operational-profile-balanced-soc-closed-source.csv)
- [combined/operational-profile-noise-reduction-closed-source.csv](combined/operational-profile-noise-reduction-closed-source.csv)
- [combined/operational-profile-high-safety-open-source-pro.csv](combined/operational-profile-high-safety-open-source-pro.csv)
- [combined/operational-profile-balanced-soc-open-source-pro.csv](combined/operational-profile-balanced-soc-open-source-pro.csv)
- [combined/operational-profile-noise-reduction-open-source-pro.csv](combined/operational-profile-noise-reduction-open-source-pro.csv)
- [combined/operational-profile-high-safety-open-source-consumer.csv](combined/operational-profile-high-safety-open-source-consumer.csv)
- [combined/operational-profile-balanced-soc-open-source-consumer.csv](combined/operational-profile-balanced-soc-open-source-consumer.csv)
- [combined/operational-profile-noise-reduction-open-source-consumer.csv](combined/operational-profile-noise-reduction-open-source-consumer.csv)

Additional documentation:

- [OPERATIONAL_PROFILES.md](OPERATIONAL_PROFILES.md) — extended operational profile tables
- [BENCHMARK.md](BENCHMARK.md) — benchmark setup details
- [SCORING.md](SCORING.md) — scoring details

The README intentionally contains the main operational summary so visitors do not need to read the extended profile page first.

"""
    text = replace_generated_block(
        text,
        GENERATED_FULL_DATA_START,
        GENERATED_FULL_DATA_END,
        full_section,
        fallback_start="## Full Data",
        fallback_end="## Related",
    )
    
    # Update chart narrative section
    chart_narrative = f"""This chart puts the three operational profile leaders next to the `always-inc` safety baseline. Each group shows Balanced OTS, Critical Miss Rate, and False Review Load with value labels, so the trade-off is visible without reading the full tables.

{generate_chart_narrative(profile_rows, tier_profile_rows)}

### 2. Operational Profile Summary by Model Tier

![Operational Profile Summary by Model Tier](charts/operational-profile-summary-by-tier.png)

This chart shows the same operational profiles split by deployment tier. Each cell uses the same guardrails as the global profile tables and shows the current profile leader within that tier, plus Balanced OTS, Critical Miss Rate, and False Review Load. Empty cells would mean no model in that tier cleared the current guardrails."""
    
    text = replace_generated_block(
        text,
        GENERATED_CHART_NARRATIVE_START,
        GENERATED_CHART_NARRATIVE_END,
        chart_narrative,
        fallback_start="### 1. Operational Profile Summary",
        fallback_end="### 2. Operational Profile Summary by Model Tier",
    )

    text = re.sub(
        r"## Operational Profiles\n.*?\n(?=## Incomplete / Dropped Model Attempts)",
        render_operational_profiles_section(models, profile_rows) + "\n",
        text,
        flags=re.S,
    )
    text = update_static_readme_counts(text, models)
    
    readme.write_text(text)

def main():
    rows = load_rows()
    baselines = [r for r in rows if r["tier"] == "baseline"]
    models = [r for r in rows if r["tier"] != "baseline"]
    tiers, tier_lookup = load_tiers()
    validate_tiers(models, tiers, tier_lookup)
    attach_estimated_costs(rows)
    profile_rows = write_profile_csvs(models)
    tier_profile_rows = write_tier_profile_csvs(models, tiers)
    write_tier_summary_csv(models, tiers, tier_profile_rows)
    write_baseline_csv(baselines)
    plot_profile_summary(profile_rows, baselines)
    plot_tier_profile_summary(tiers, tier_profile_rows)
    scatter_charts(models, baselines, tiers)
    update_readme(models, tiers, profile_rows, tier_profile_rows)
    print("✓ operational profile CSVs")
    print("✓ tier-specific operational profile CSVs")
    print("✓ operational-profile-summary.png")
    print("✓ operational-profile-summary-by-tier.png")
    print("✓ critical-miss-vs-false-review.png")
    print("✓ balanced-ots-vs-false-review.png")
    print("✓ cw-vs-balanced-ots.png")
    print("✓ full-labeled scatter appendix charts")


if __name__ == "__main__":
    main()
