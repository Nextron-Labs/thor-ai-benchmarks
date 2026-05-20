#!/usr/bin/env python3
"""Onboard new benchmark models: detect missing pricing/tier mappings and update them."""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = REPO_ROOT / "results"
COMBINED_DIR = REPO_ROOT / "combined"
SCRIPTS_DIR = REPO_ROOT / "scripts"

TIERS_PATH = SCRIPTS_DIR / "model_tiers.json"
COSTS_PATH = SCRIPTS_DIR / "openrouter_costs.py"
PRICING_PATH = SCRIPTS_DIR / "openrouter_pricing_snapshot.json"


def load_json(path):
    return json.loads(path.read_text())


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def load_tiers():
    data = load_json(TIERS_PATH)
    all_models = set()
    tier_lookup = {}
    for tier_key, tier_data in data.get("tiers", {}).items():
        for m in tier_data["models"]:
            all_models.add(m)
            tier_lookup[m] = tier_key
    return all_models, tier_lookup, data.get("excluded", [])


def load_bench_to_openrouter():
    import importlib.util
    spec = importlib.util.spec_from_file_location("openrouter_costs", COSTS_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.BENCH_TO_OPENROUTER


def load_pricing():
    return load_json(PRICING_PATH).get("models", {})


def load_leaderboard_models():
    """Get models currently in combined leaderboard."""
    lb_path = COMBINED_DIR / "leaderboard.json"
    if not lb_path.exists():
        return set()
    lb = load_json(lb_path)
    return {m["model"] for m in lb if m.get("tier") != "baseline"}


def load_result_models():
    """Scan all results directories for model names."""
    models = set()
    for report_dir in RESULTS_DIR.iterdir():
        if not report_dir.is_dir():
            continue
        for result_file in report_dir.glob("*.json"):
            model_name = result_file.stem
            if model_name in ("combined", "leaderboard"):
                continue
            models.add(model_name)
    return models


def fetch_openrouter_pricing():
    """Fetch current OpenRouter pricing."""
    try:
        result = subprocess.run(
            ["curl", "-s", "https://openrouter.ai/api/v1/models"],
            capture_output=True, text=True, timeout=30
        )
        data = json.loads(result.stdout)
        pricing = {}
        for m in data.get("data", []):
            pricing[m["id"]] = {
                "prompt": float(m["pricing"]["prompt"]),
                "completion": float(m["pricing"]["completion"])
            }
        return pricing
    except Exception as e:
        print(f"Warning: Failed to fetch OpenRouter pricing: {e}")
        return {}


def infer_openrouter_id(bench_name):
    """Infer OpenRouter model ID from benchmark model name."""
    # Common patterns
    name = bench_name

    # Provider prefixes
    if name.startswith("gemini-"):
        return f"google/{name}"
    if name.startswith("gpt-"):
        return f"openai/{name}"
    if name.startswith("claude-"):
        return f"anthropic/{name}"
    if name.startswith("grok-"):
        # Handle special cases
        if name == "grok-4-openrouter":
            return "x-ai/grok-4"
        return f"x-ai/{name}"
    if name.startswith("deepseek-"):
        # Map version variants
        if name == "deepseek-v3.1":
            return "deepseek/deepseek-chat-v3.1"
        if name == "deepseek-v3.2":
            return "deepseek/deepseek-chat-v3-0324"
        if name == "deepseek-v4-flash":
            return "deepseek/deepseek-chat-v3-0324"
        if name == "deepseek-v4-pro":
            return "deepseek/deepseek-chat"
        return f"deepseek/{name}"
    if name.startswith("qwen"):
        if name == "qwen35-397b":
            return "qwen/qwen3.5-397b-a17b"
        if name == "qwen3-235b-a22b":
            return "qwen/qwen3-235b-a22b-2507"
        return f"qwen/{name}"
    if name.startswith("glm-"):
        return f"z-ai/{name}"
    if name.startswith("kimi-"):
        return f"moonshotai/{name}"
    if name.startswith("gemma"):
        # Handle gemma4 -> gemini-4 mapping
        if name.startswith("gemma4"):
            return f"google/{name.replace('gemma4', 'gemma-4')}-it"
        return f"google/{name}"
    if name.startswith("llama-"):
        return f"meta-llama/{name}-instruct"
    if name.startswith("mistral-"):
        return f"mistralai/{name}"
    if name.startswith("minimax-"):
        return f"minimax/{name}"
    if name.startswith("nemotron-"):
        if name == "nemotron-3-super-120b":
            return "nvidia/nemotron-3-super-120b-a12b"
        if name == "nemotron-3-nano-omni":
            return "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
        return f"nvidia/{name}"
    if name.startswith("mercury-"):
        return f"inception/{name}"
    if name.startswith("mimo-"):
        return f"xiaomi/{name}"
    if name.startswith("devstral-"):
        return f"mistralai/{name}"

    return None


def infer_tier(bench_name, or_id=None):
    """Infer tier from model name or OpenRouter ID."""
    name = bench_name.lower()

    # Open source consumer (can run on consumer hardware)
    consumer_models = {
        "gemma4-31b", "qwen3.6-35b", "qwen3.5-9b", "devstral-small",
        "llama-3.1-8b", "llama-3.1-70b"
    }
    if name in consumer_models:
        return "open_source_consumer"

    # Check for indicators
    if any(x in name for x in ["70b", "120b", "235b", "397b", "pro-", "max-"]):
        return "open_source_pro"

    # Free models on OpenRouter are typically open source
    if or_id and ":free" in or_id:
        return "open_source_consumer"

    # Default closed source for vendor APIs
    if any(name.startswith(p) for p in ["gpt-", "claude-", "gemini-", "grok-", "o1-", "o3-"]):
        return "closed_source"

    # Default based on size/heuristics
    return "open_source_pro"


def main():
    print("=== Model Onboarding Check ===\n")

    # Load current state
    tiered_models, tier_lookup, excluded = load_tiers()
    b2o = load_bench_to_openrouter()
    pricing = load_pricing()
    leaderboard_models = load_leaderboard_models()
    result_models = load_result_models()

    # Find new models
    all_known = tiered_models | set(b2o.keys())
    new_models = result_models - all_known - set(excluded)

    if new_models:
        print(f"🆕 NEW MODELS detected in results: {sorted(new_models)}\n")

    # Fetch fresh pricing
    print("Fetching current OpenRouter pricing...")
    fresh_pricing = fetch_openrouter_pricing()

    # Check each model in results
    missing_mapping = []
    missing_pricing = []
    missing_tier = []

    for model in sorted(result_models):
        if model in excluded:
            continue

        if model not in b2o:
            missing_mapping.append(model)

        or_id = b2o.get(model) or infer_openrouter_id(model)
        if or_id and or_id not in pricing:
            missing_pricing.append((model, or_id))

        if model not in tiered_models and model not in excluded:
            missing_tier.append(model)

    # Report findings
    if not (missing_mapping or missing_pricing or missing_tier):
        print("✓ All models have complete mapping, pricing, and tier assignments.")
        print(f"  Total: {len(tiered_models)} tiered, {len(b2o)} mapped, {len(pricing)} priced")
        return

    print("\n=== MISSING ===\n")

    if missing_mapping:
        print("BENCH_TO_OPENROUTER mapping needed:")
        for m in missing_mapping:
            inferred = infer_openrouter_id(m)
            print(f"  \"{m}\": \"{inferred or '???'}\",")
        print()

    if missing_pricing:
        print("OpenRouter pricing needed:")
        for model, or_id in missing_pricing:
            fresh = fresh_pricing.get(or_id, {})
            if fresh:
                p = fresh.get("prompt", "?")
                c = fresh.get("completion", "?")
                print(f'    "{or_id}": {{')
                print(f'      "prompt": {p},')
                print(f'      "completion": {c}')
                print(f'    }},  # <- {model}')
            else:
                print(f"  {model}: {or_id} (not found on OpenRouter)")
        print()

    if missing_tier:
        print("Tier assignment needed:")
        for m in missing_tier:
            inferred_tier = infer_tier(m, b2o.get(m))
            print(f"  {m} -> {inferred_tier}")
        print()

    # Offer to auto-fix
    if "--auto" in sys.argv:
        print("=== AUTO-FIXING ===\n")

        # Update BENCH_TO_OPENROUTER
        if missing_mapping:
            print(f"Adding {len(missing_mapping)} mappings to openrouter_costs.py...")
            # Read current file
            content = COSTS_PATH.read_text()
            # Find the last entry before closing brace
            lines = content.split('\n')
            insert_idx = None
            for i, line in enumerate(lines):
                if line.strip().startswith('}'):
                    insert_idx = i
                    break

            new_mappings = []
            for m in sorted(missing_mapping):
                or_id = infer_openrouter_id(m)
                if or_id:
                    new_mappings.append(f'    "{m}": "{or_id}",')

            if new_mappings:
                lines[insert_idx:insert_idx] = new_mappings
                COSTS_PATH.write_text('\n'.join(lines))
                print(f"  Added: {', '.join(missing_mapping)}")

        # Update pricing
        if missing_pricing and fresh_pricing:
            print(f"Adding pricing for {len(missing_pricing)} models...")
            current = load_json(PRICING_PATH)
            for model, or_id in missing_pricing:
                if or_id in fresh_pricing:
                    current["models"][or_id] = fresh_pricing[or_id]
                    print(f"  Added: {or_id}")
            # Update timestamp
            from datetime import datetime
            current["fetched_at"] = datetime.utcnow().isoformat() + "+00:00"
            save_json(PRICING_PATH, current)

        # Update tiers
        if missing_tier:
            print(f"Adding tier assignments for {len(missing_tier)} models...")
            current = load_json(TIERS_PATH)
            for m in missing_tier:
                tier = infer_tier(m, b2o.get(m))
                if tier in current["tiers"]:
                    current["tiers"][tier]["models"].append(m)
                    print(f"  {m} -> {tier}")
            save_json(TIERS_PATH, current)

        print("\n✓ Auto-fix complete. Regenerating all charts...")
        
        # Regenerate all charts
        import subprocess
        
        scripts = [
            "scripts/quality-vs-cost.py",
            "scripts/quality-vs-speed.py",
            "scripts/generate_charts.py",
            "scripts/operational_profiles.py",
        ]
        
        for script in scripts:
            script_path = REPO_ROOT / script
            if script_path.exists():
                print(f"  Running {script}...")
                result = subprocess.run(["python3", str(script_path)], cwd=REPO_ROOT, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"    WARNING: {script} failed")
                    print(result.stderr)
                else:
                    print(f"    ✓ {script}")
        
        print("\n✓ All charts regenerated.")


if __name__ == "__main__":
    main()