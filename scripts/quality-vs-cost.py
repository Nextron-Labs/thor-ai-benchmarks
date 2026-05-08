#!/usr/bin/env python3
"""Generate quality-vs-cost scatter chart for THOR benchmarks.

Reads leaderboard data and exclusion list from model_tiers.json,
fetches live pricing from OpenRouter, and produces charts/quality-vs-cost.png.
"""
import json, sys
from pathlib import Path

import urllib.request
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

REPO_ROOT = Path(__file__).resolve().parent.parent
COMBINED_DIR = REPO_ROOT / "combined"
CHARTS_DIR = REPO_ROOT / "charts"
TIERS_PATH = REPO_ROOT / "scripts" / "model_tiers.json"

# ── Benchmark model name → OpenRouter model ID mapping ──────────
BENCH_TO_OR = {
    "gemma4-31b": "google/gemma-4-31b-it",
    "llama-3.1-70b": "meta-llama/llama-3.1-70b-instruct",
    "llama-3.1-8b": "meta-llama/llama-3.1-8b-instruct",
    "qwen3.5-9b": "qwen/qwen3.5-9b",
    "ministral-14b": "mistralai/ministral-14b-2512",
    "devstral-small": "mistralai/devstral-small",
    "deepseek-v4-pro": "deepseek/deepseek-chat",
    "deepseek-v4-flash": "deepseek/deepseek-chat-v3-0324",
    "deepseek-v3.2": "deepseek/deepseek-chat-v3-0324",
    "deepseek-v3.1": "deepseek/deepseek-chat-v3.1",
    "qwen35-397b": "qwen/qwen3.5-397b-a17b",
    "glm-5": "z-ai/glm-5",
    "glm-5.1": "z-ai/glm-5.1",
    "mistral-nemo": "mistralai/mistral-nemo",
    "nemotron-3-super-120b": "nvidia/nemotron-3-super-120b-a12b",
    "nemotron-3-nano-omni": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "kimi-k2.6": "moonshotai/kimi-k2.6",
    "kimi-k2.5": "moonshotai/kimi-k2.5",
    "qwen3.5-plus-20260420": "qwen/qwen3.5-plus-20260420",
    "gemini-2.5-pro": "google/gemini-2.5-pro",
    "gemini-3.1-pro": "google/gemini-3.1-pro-preview",
    "grok-4.20": "x-ai/grok-4.20",
    "grok-4.1-fast": "x-ai/grok-4.1-fast",
    "grok-4-fast": "x-ai/grok-4-fast",
    "gpt-5": "openai/gpt-5",
    "claude-opus-4.6": "anthropic/claude-opus-4.6",
    "grok-4-openrouter": "x-ai/grok-4",
    "qwen3.6-plus": "qwen/qwen3.6-max-preview",
    "qwen3.6-max": "qwen/qwen3.6-max-preview",
    "claude-sonnet-4.6": "anthropic/claude-sonnet-4.6",
    "gpt-5.4": "openai/gpt-5.4",
    "gpt-5-nano": "openai/gpt-5-nano",
    "mimo-v2-pro": "xiaomi/mimo-v2-pro",
    "gpt-5.5": "openai/gpt-5.5",
    "claude-opus-4.5": "anthropic/claude-opus-4.5",
    "minimax-m2.7": "minimax/minimax-m2.7",
    "gpt-5-mini": "openai/gpt-5-mini",
    "minimax-m2.5": "minimax/minimax-m2.5",
    "gemini-2.5-flash": "google/gemini-2.5-flash",
    "gpt-oss-120b": "openai/gpt-oss-120b",
    "gpt-5.4-nano": "openai/gpt-5.4-nano",
    "claude-haiku-4.5": "anthropic/claude-haiku-4.5",
    "gpt-5.4-mini": "openai/gpt-5.4-mini",
    "qwen3.6-flash": "qwen/qwen3.6-flash",
    "gpt-oss-20b": "openai/gpt-oss-20b",
    "qwen3-235b-a22b": "qwen/qwen3-235b-a22b-2507",
    "mercury-2": "inception/mercury-2",
    "claude-sonnet-4.5": "anthropic/claude-sonnet-4.5",
    "gemini-3.1-flash-lite": "google/gemini-3.1-flash-lite",
    "grok-4.3": "x-ai/grok-4.3",
}

# ── Cost estimation parameters ────────────────────────────────────
# Input/output token split ratio (empirical estimate: ~85% input, ~15% output)
INPUT_RATIO = 0.85
OUTPUT_RATIO = 0.15


def main():
    # Load exclusion list from model_tiers.json
    with open(TIERS_PATH) as f:
        tiers_config = json.load(f)
    excluded = set(tiers_config.get("excluded", []))

    # Load tier lookup
    tier_lookup = {}
    tier_names = list(tiers_config.get("tiers", {}).keys())
    for tier_key, tier_data in tiers_config.get("tiers", {}).items():
        for m in tier_data["models"]:
            tier_lookup[m] = tier_key

    # Fetch live pricing from OpenRouter
    url = "https://openrouter.ai/api/v1/models"
    req = urllib.request.Request(url, headers={"User-Agent": "mjolnir-benchmark"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        or_data = json.loads(resp.read())["data"]
    or_pricing = {}
    for m in or_data:
        pi = float(m["pricing"]["prompt"]) if m["pricing"]["prompt"] else 0
        ci = float(m["pricing"]["completion"]) if m["pricing"]["completion"] else 0
        or_pricing[m["id"]] = {"prompt": pi, "completion": ci}

    # Build price lookup for benchmark models
    model_prices = {}
    for name, or_id in BENCH_TO_OR.items():
        if name in excluded:
            continue
        if or_id in or_pricing:
            model_prices[name] = or_pricing[or_id]

    # Load leaderboard
    lb_path = COMBINED_DIR / "leaderboard.json"
    with open(lb_path) as f:
        lb = json.load(f)

    # Count total findings scored across all reports
    n_findings_total = max(int(m['n']) for m in lb if m['model'] not in excluded)

    results = []
    missing_price = []
    for m in lb:
        name = m['model']
        if name in excluded:
            continue
        cw_pct = float(m['cw_pct'])
        tier = m['tier']
        total_tokens = int(m.get('total_tokens', 0))
        if name not in model_prices:
            missing_price.append(name)
            continue
        p = model_prices[name]
        total_input = total_tokens * INPUT_RATIO
        total_output = total_tokens * OUTPUT_RATIO
        cost = (total_input * p['prompt']) + (total_output * p['completion'])
        cost_cents = cost * 100
        results.append({'model': name, 'cw_pct': cw_pct, 'cost_cents': cost_cents, 'tier': tier})
    if missing_price:
        print(f"  Warning: no OpenRouter pricing for {len(missing_price)} models: {missing_price}")

    # Generate chart
    tier_colors = {'closed_source': '#e74c3c', 'open_source_pro': '#3498db', 'open_source_consumer': '#2ecc71'}
    tier_markers = {'closed_source': 'D', 'open_source_pro': 's', 'open_source_consumer': 'o'}
    fig, ax = plt.subplots(figsize=(14, 10))

    for tier, color in tier_colors.items():
        tier_data = [r for r in results if r['tier'] == tier]
        x = [r['cost_cents'] for r in tier_data]
        y = [r['cw_pct'] for r in tier_data]
        ax.scatter(x, y, c=color, label=tier.replace('_', ' ').title(),
                   s=120, alpha=0.75, marker=tier_markers[tier])
        for r in tier_data:
            ax.annotate(r['model'], (r['cost_cents'], r['cw_pct']),
                        fontsize=7.5, ha='left', va='bottom',
                        xytext=(3, 3), textcoords='offset points')

    n_models = len(results)
    ax.set_xlabel('Estimated Cost per Run (¢)', fontsize=12)
    ax.set_ylabel('Quality Score (CW %)', fontsize=12)
    ax.set_title(f'THOR Benchmark: Quality vs Cost\n({n_models} models · {n_findings_total} findings · cost based on actual token usage)', fontsize=14)
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)
    ax.axhline(y=38, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
    ax.axvline(x=5, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
    plt.tight_layout()

    CHARTS_DIR.mkdir(exist_ok=True)
    fig.savefig(CHARTS_DIR / 'quality-vs-cost.png', dpi=150)
    print(f"✓ quality-vs-cost.png ({n_models} models, excluded: {excluded})")


if __name__ == "__main__":
    main()