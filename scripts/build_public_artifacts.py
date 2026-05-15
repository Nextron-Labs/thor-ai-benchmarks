#!/usr/bin/env python3
"""Regenerate all public benchmark artifacts from the committed source data."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

STEPS = [
    "scripts/operational_profiles.py",
    "scripts/generate_charts.py",
    "scripts/quality-vs-speed.py",
    "scripts/quality-vs-cost.py",
    "scripts/generate_site_data.py",
    "scripts/validate_public_artifacts.py",
]


def main() -> int:
    cache_dir = ROOT / ".cache-public-artifacts"
    cache_dir.mkdir(exist_ok=True)
    env = dict(os.environ)
    env.setdefault("MPLCONFIGDIR", str(cache_dir / "matplotlib"))
    env.setdefault("XDG_CACHE_HOME", str(cache_dir / "xdg"))
    Path(env["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
    Path(env["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)

    for step in STEPS:
        step_path = ROOT / step
        print(f"==> {step}")
        subprocess.run([sys.executable, str(step_path)], cwd=ROOT, check=True, env=env)
    print("✓ public benchmark artifacts are up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
