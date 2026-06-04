#!/usr/bin/env python3
"""Sync generated leaderboard tier fields from scripts/model_tiers.json."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TIERS_PATH = ROOT / "scripts" / "model_tiers.json"
LEADERBOARD_JSON = ROOT / "combined" / "leaderboard.json"
LEADERBOARD_CSV = ROOT / "combined" / "leaderboard.csv"


def load_tier_lookup() -> dict[str, str]:
    payload = json.loads(TIERS_PATH.read_text())
    lookup: dict[str, str] = {}
    duplicates: dict[str, list[str]] = {}

    for tier_key, tier_data in payload["tiers"].items():
        for model in tier_data["models"]:
            if model in lookup:
                duplicates.setdefault(model, [lookup[model]]).append(tier_key)
            lookup[model] = tier_key

    if duplicates:
        details = ", ".join(
            f"{model}: {'/'.join(tiers)}" for model, tiers in sorted(duplicates.items())
        )
        raise SystemExit(f"Duplicate model tier assignments in {TIERS_PATH}: {details}")

    return lookup


def desired_tier(row: dict[str, object], tier_lookup: dict[str, str]) -> str:
    if row.get("rank") == "baseline" or row.get("tier") == "baseline":
        return "baseline"

    model = str(row["model"])
    try:
        return tier_lookup[model]
    except KeyError as exc:
        raise SystemExit(
            f"{model} is present in the public leaderboard but missing from {TIERS_PATH}"
        ) from exc


def sync_json(tier_lookup: dict[str, str], check: bool) -> int:
    rows = json.loads(LEADERBOARD_JSON.read_text())
    changed = 0

    for row in rows:
        tier = desired_tier(row, tier_lookup)
        if row.get("tier") != tier:
            row["tier"] = tier
            changed += 1

    if changed and not check:
        LEADERBOARD_JSON.write_text(json.dumps(rows, indent=2) + "\n")

    return changed


def sync_csv(tier_lookup: dict[str, str], check: bool) -> int:
    with LEADERBOARD_CSV.open(newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames

    if not fieldnames:
        raise SystemExit(f"{LEADERBOARD_CSV} has no CSV header")

    changed = 0
    for row in rows:
        tier = desired_tier(row, tier_lookup)
        if row.get("tier") != tier:
            row["tier"] = tier
            changed += 1

    if changed and not check:
        with LEADERBOARD_CSV.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if leaderboard tiers are stale without rewriting files",
    )
    args = parser.parse_args()

    tier_lookup = load_tier_lookup()
    json_changed = sync_json(tier_lookup, args.check)
    csv_changed = sync_csv(tier_lookup, args.check)
    total_changed = json_changed + csv_changed

    if args.check and total_changed:
        raise SystemExit(
            f"Leaderboard tiers are stale: {json_changed} JSON rows and {csv_changed} CSV rows differ"
        )

    if total_changed:
        print(f"✓ synced leaderboard tiers ({json_changed} JSON rows, {csv_changed} CSV rows)")
    else:
        print("✓ leaderboard tiers already match scripts/model_tiers.json")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
