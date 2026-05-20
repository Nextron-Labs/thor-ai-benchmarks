#!/usr/bin/env python3
"""Shared OpenRouter pricing helpers for THOR benchmark cost estimates."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
PRICING_SNAPSHOT_PATH = Path(__file__).resolve().parent / "openrouter_pricing_snapshot.json"

# Benchmark model name -> OpenRouter model ID mapping.
BENCH_TO_OPENROUTER = {
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
    "gemini-3.5-flash": "google/gemini-3.5-flash",
    "grok-4.3": "x-ai/grok-4.3",
}

# Empirical estimate for total token split across prompt and completion tokens.
INPUT_RATIO = 0.85
OUTPUT_RATIO = 0.15


def load_pricing_snapshot():
    """Load committed OpenRouter pricing data keyed by OpenRouter model ID."""
    payload = json.loads(PRICING_SNAPSHOT_PATH.read_text())
    return payload.get("models", {})


def estimate_run_cost_cents(model_name, total_tokens, pricing_by_id=None):
    """Estimate benchmark-run cost in cents from total token usage."""
    if not total_tokens:
        return None

    pricing_by_id = pricing_by_id or load_pricing_snapshot()
    openrouter_id = BENCH_TO_OPENROUTER.get(model_name)
    if not openrouter_id:
        return None

    price = pricing_by_id.get(openrouter_id)
    if not price:
        return None

    total_input = total_tokens * INPUT_RATIO
    total_output = total_tokens * OUTPUT_RATIO
    cost = (total_input * price["prompt"]) + (total_output * price["completion"])
    return round(cost * 100, 4)
