# Operational Profiles — Extended Tables

This is the extended operational profile reference for the THOR AI benchmark. The main summary now lives in [README.md](README.md); this page is kept for quick access to the profile constraints and generated tables.

## Baseline Reference

| Strategy | CW% | BalOTS | CritMiss | ThreatCap | FalseRev | FalseEsc | Cost/Run |
|---|---:|---:|---:|---:|---:|---:|---:|
| `always-fp` | 28.7% | -58.3% | 100.0% | 0.0% | 0.0% | 0.0% | $0.00 |
| `always-inc` | 24.5% | 38.3% | 0.0% | 100.0% | 100.0% | 0.0% | $0.00 |
| `always-tp` | 16.8% | 25.0% | 0.0% | 100.0% | 100.0% | 100.0% | $0.00 |

Baselines are references, not recommendations. `always-fp` suppresses everything and is dangerous; `always-inc` sends everything to review and is safe but operationally weak; `always-tp` escalates everything and is noisy.

## Profile 1: High-Safety

**Use case:** Environments where missing any real incident is unacceptable.

**Requirements:** Complete coverage, Critical Miss Rate ≤ 5%, Threat Capture Rate ≥ 95%, False Review Load ≤ 75%.

**Recommendation guardrail:** high-safety recommendations must still reduce review load meaningfully; near-`always-inc` behavior is excluded from this table.

**Ranking:** Balanced OTS descending, then False Review Load ascending.

| # | Model | CW% | BalOTS | CritMiss | ThreatCap | FalseRev | FalseEsc | Cost/Run | AvgTime |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | gemini-3.1-flash-lite | 71.3% | 72.8% | 0.0% | 100.0% | 27.6% | 1.3% | — | 1.87s |
| 2 | qwen3-235b-a22b | 61.1% | 68.4% | 0.0% | 100.0% | 50.0% | 3.9% | $0.00 | 31.93s |
| 3 | gemma4-31b | 66.4% | 66.2% | 0.0% | 100.0% | 36.8% | 7.9% | $0.00 | 16.86s |
| 4 | glm-5.1 | 67.3% | 66.1% | 0.0% | 100.0% | 34.2% | 7.9% | — | 43.93s |
| 5 | kimi-k2.5 | 68.7% | 65.4% | 2.3% | 97.7% | 31.6% | 6.6% | — | 37.74s |
| 6 | deepseek-v4-pro | 65.3% | 65.2% | 0.0% | 100.0% | 31.6% | 5.3% | — | 36.63s |
| 7 | glm-5 | 64.7% | 64.7% | 0.0% | 100.0% | 34.2% | 7.9% | — | 38.18s |
| 8 | gpt-5.5 | 58.4% | 64.6% | 0.0% | 100.0% | 40.8% | 6.6% | — | 55.85s |
| 9 | gemini-3.1-pro | 67.1% | 63.8% | 2.3% | 97.7% | 36.8% | 3.9% | — | 24.97s |
| 10 | kimi-k2.6 | 63.8% | 63.2% | 0.0% | 100.0% | 32.9% | 3.9% | — | 63.32s |
| 11 | deepseek-v4-flash | 63.7% | 62.3% | 0.0% | 100.0% | 31.6% | 9.2% | $0.10 | 25.47s |
| 12 | qwen35-397b | 57.6% | 61.9% | 0.0% | 100.0% | 43.4% | 2.6% | — | 46.97s |
| 13 | claude-sonnet-4.5 | 61.6% | 61.8% | 0.0% | 100.0% | 42.1% | 9.2% | — | 10.49s |
| 14 | grok-4.3 | 60.5% | 61.3% | 2.3% | 97.7% | 39.5% | 7.9% | — | 17.10s |
| 15 | claude-opus-4.5 | 63.5% | 60.8% | 2.3% | 97.7% | 34.2% | 10.5% | — | 9.80s |
| 16 | minimax-m2.7 | 57.9% | 60.6% | 2.3% | 97.7% | 36.8% | 2.6% | — | 21.26s |
| 17 | deepseek-v3.2 | 55.4% | 60.1% | 0.0% | 100.0% | 52.6% | 10.5% | $0.32 | 73.10s |
| 18 | gemini-2.5-pro | 60.4% | 59.7% | 0.0% | 100.0% | 38.2% | 21.1% | — | 15.82s |
| 19 | claude-opus-4.6 | 61.3% | 59.7% | 0.0% | 100.0% | 42.1% | 9.2% | — | 11.52s |
| 20 | gpt-5 | 55.5% | 59.6% | 0.0% | 100.0% | 44.7% | 5.3% | — | 28.34s |
| 21 | claude-sonnet-4.6 | 57.3% | 59.6% | 0.0% | 100.0% | 50.0% | 9.2% | — | 12.15s |
| 22 | grok-4.20 | 59.6% | 58.6% | 4.5% | 95.5% | 39.5% | 1.3% | $2.23 | 9.46s |
| 23 | deepseek-v3.1 | 54.4% | 57.4% | 0.0% | 100.0% | 48.7% | 7.9% | — | 18.42s |
| 24 | nemotron-3-super-120b | 53.7% | 57.0% | 0.0% | 100.0% | 44.7% | 6.6% | — | 43.50s |
| 25 | gpt-5-mini | 47.6% | 55.9% | 0.0% | 100.0% | 68.4% | 5.3% | — | 21.06s |
| 26 | gpt-5.4 | 49.9% | 55.8% | 0.0% | 100.0% | 46.1% | 0.0% | — | 7.39s |
| 27 | llama-3.1-70b | 51.9% | 55.0% | 2.3% | 97.7% | 55.3% | 26.3% | $0.00 | 15.29s |
| 28 | minimax-m2.5 | 53.2% | 54.7% | 0.0% | 100.0% | 44.7% | 0.0% | $0.16 | 19.88s |
| 29 | gemini-2.5-flash | 52.0% | 51.0% | 2.3% | 97.7% | 51.3% | 15.8% | — | 3.07s |
| 30 | devstral-small | 45.1% | 48.2% | 4.5% | 95.5% | 68.4% | 11.8% | — | 1.52s |
| 31 | mercury-2 | 43.8% | 44.0% | 4.5% | 95.5% | 55.3% | 6.6% | — | 1.63s |

**Matched:** 31 / 47 complete models.

**Interpretation:** Under these constraints, `gemini-3.1-flash-lite` is the current profile leader. `llama-3.1-8b` is excluded because its False Review Load is 86.8%.

## Profile 2: Balanced SOC

**Use case:** General SOC operations where a balance between safety and efficiency is needed.

**Requirements:** Complete coverage, Critical Miss Rate ≤ 15%, Threat Capture Rate ≥ 85%, False Review Load ≤ 75%.

**Ranking:** Balanced OTS descending.

| # | Model | CW% | BalOTS | CritMiss | ThreatCap | FalseRev | FalseEsc | Cost/Run | AvgTime |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | gemini-3.1-flash-lite | 71.3% | 72.8% | 0.0% | 100.0% | 27.6% | 1.3% | — | 1.87s |
| 2 | qwen3-235b-a22b | 61.1% | 68.4% | 0.0% | 100.0% | 50.0% | 3.9% | $0.00 | 31.93s |
| 3 | gemma4-31b | 66.4% | 66.2% | 0.0% | 100.0% | 36.8% | 7.9% | $0.00 | 16.86s |
| 4 | glm-5.1 | 67.3% | 66.1% | 0.0% | 100.0% | 34.2% | 7.9% | — | 43.93s |
| 5 | kimi-k2.5 | 68.7% | 65.4% | 2.3% | 97.7% | 31.6% | 6.6% | — | 37.74s |
| 6 | deepseek-v4-pro | 65.3% | 65.2% | 0.0% | 100.0% | 31.6% | 5.3% | — | 36.63s |
| 7 | glm-5 | 64.7% | 64.7% | 0.0% | 100.0% | 34.2% | 7.9% | — | 38.18s |
| 8 | gpt-5.5 | 58.4% | 64.6% | 0.0% | 100.0% | 40.8% | 6.6% | — | 55.85s |
| 9 | gemini-3.1-pro | 67.1% | 63.8% | 2.3% | 97.7% | 36.8% | 3.9% | — | 24.97s |
| 10 | kimi-k2.6 | 63.8% | 63.2% | 0.0% | 100.0% | 32.9% | 3.9% | — | 63.32s |
| 11 | deepseek-v4-flash | 63.7% | 62.3% | 0.0% | 100.0% | 31.6% | 9.2% | $0.10 | 25.47s |
| 12 | qwen35-397b | 57.6% | 61.9% | 0.0% | 100.0% | 43.4% | 2.6% | — | 46.97s |
| 13 | claude-sonnet-4.5 | 61.6% | 61.8% | 0.0% | 100.0% | 42.1% | 9.2% | — | 10.49s |
| 14 | grok-4.3 | 60.5% | 61.3% | 2.3% | 97.7% | 39.5% | 7.9% | — | 17.10s |
| 15 | claude-opus-4.5 | 63.5% | 60.8% | 2.3% | 97.7% | 34.2% | 10.5% | — | 9.80s |
| 16 | minimax-m2.7 | 57.9% | 60.6% | 2.3% | 97.7% | 36.8% | 2.6% | — | 21.26s |
| 17 | deepseek-v3.2 | 55.4% | 60.1% | 0.0% | 100.0% | 52.6% | 10.5% | $0.32 | 73.10s |
| 18 | gemini-2.5-pro | 60.4% | 59.7% | 0.0% | 100.0% | 38.2% | 21.1% | — | 15.82s |
| 19 | claude-opus-4.6 | 61.3% | 59.7% | 0.0% | 100.0% | 42.1% | 9.2% | — | 11.52s |
| 20 | gpt-5 | 55.5% | 59.6% | 0.0% | 100.0% | 44.7% | 5.3% | — | 28.34s |
| 21 | claude-sonnet-4.6 | 57.3% | 59.6% | 0.0% | 100.0% | 50.0% | 9.2% | — | 12.15s |
| 22 | grok-4.20 | 59.6% | 58.6% | 4.5% | 95.5% | 39.5% | 1.3% | $2.23 | 9.46s |
| 23 | ring-2.6-1t | 61.3% | 58.2% | 6.8% | 93.2% | 39.5% | 7.9% | — | 40.47s |
| 24 | deepseek-v3.1 | 54.4% | 57.4% | 0.0% | 100.0% | 48.7% | 7.9% | — | 18.42s |
| 25 | nemotron-3-super-120b | 53.7% | 57.0% | 0.0% | 100.0% | 44.7% | 6.6% | — | 43.50s |
| 26 | gpt-5-mini | 47.6% | 55.9% | 0.0% | 100.0% | 68.4% | 5.3% | — | 21.06s |
| 27 | gpt-5.4 | 49.9% | 55.8% | 0.0% | 100.0% | 46.1% | 0.0% | — | 7.39s |
| 28 | grok-4-openrouter | 62.4% | 55.7% | 6.8% | 93.2% | 32.9% | 10.5% | — | 24.82s |
| 29 | llama-3.1-70b | 51.9% | 55.0% | 2.3% | 97.7% | 55.3% | 26.3% | $0.00 | 15.29s |
| 30 | minimax-m2.5 | 53.2% | 54.7% | 0.0% | 100.0% | 44.7% | 0.0% | $0.16 | 19.88s |
| 31 | grok-4.1-fast | 62.3% | 53.2% | 9.1% | 90.9% | 31.6% | 11.8% | — | 11.01s |
| 32 | grok-4-fast | 60.5% | 51.5% | 6.8% | 93.2% | 32.9% | 9.2% | — | 9.87s |
| 33 | gemini-2.5-flash | 52.0% | 51.0% | 2.3% | 97.7% | 51.3% | 15.8% | — | 3.07s |
| 34 | qwen3.5-plus-20260420 | 63.0% | 50.3% | 11.4% | 88.6% | 22.4% | 5.3% | — | 43.94s |
| 35 | qwen3.5-9b | 55.8% | 50.3% | 11.4% | 88.6% | 36.8% | 2.6% | — | 23.02s |
| 36 | gpt-5.4-mini | 52.5% | 50.1% | 6.8% | 93.2% | 46.1% | 5.3% | — | 4.44s |
| 37 | claude-haiku-4.5 | 58.1% | 48.2% | 6.8% | 93.2% | 34.2% | 9.2% | — | 5.89s |
| 38 | devstral-small | 45.1% | 48.2% | 4.5% | 95.5% | 68.4% | 11.8% | — | 1.52s |
| 39 | mimo-v2-pro | 59.8% | 47.9% | 6.8% | 93.2% | 27.6% | 13.2% | — | 7.13s |
| 40 | qwen3.6-plus | 61.3% | 47.3% | 11.4% | 88.6% | 25.0% | 3.9% | — | 41.21s |
| 41 | qwen3.6-max | 64.2% | 45.8% | 13.6% | 86.4% | 21.1% | 7.9% | — | 105.62s |
| 42 | mercury-2 | 43.8% | 44.0% | 4.5% | 95.5% | 55.3% | 6.6% | — | 1.63s |
| 43 | mistral-nemo | 38.5% | 32.3% | 9.1% | 90.9% | 61.8% | 18.4% | — | 5.90s |

**Matched:** 43 / 47 complete models.

**Interpretation:** Under these constraints, `gemini-3.1-flash-lite` currently provides the best balance in this data set.

## Profile 3: Noise-Reduction

**Use case:** High-volume alert triage where reducing review load is a priority and some miss risk is acceptable.

**Requirements:** Complete coverage, False Review Load ≤ 55%, Critical Miss Rate ≤ 20%, Balanced OTS > 0.

**Ranking:** False Review Load ascending, then Balanced OTS descending.

| # | Model | CW% | BalOTS | CritMiss | ThreatCap | FalseRev | FalseEsc | Cost/Run | AvgTime |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | qwen3.6-max | 64.2% | 45.8% | 13.6% | 86.4% | 21.1% | 7.9% | — | 105.62s |
| 2 | qwen3.5-plus-20260420 | 63.0% | 50.3% | 11.4% | 88.6% | 22.4% | 5.3% | — | 43.94s |
| 3 | qwen3.6-plus | 61.3% | 47.3% | 11.4% | 88.6% | 25.0% | 3.9% | — | 41.21s |
| 4 | gemini-3.1-flash-lite | 71.3% | 72.8% | 0.0% | 100.0% | 27.6% | 1.3% | — | 1.87s |
| 5 | mimo-v2-pro | 59.8% | 47.9% | 6.8% | 93.2% | 27.6% | 13.2% | — | 7.13s |
| 6 | kimi-k2.5 | 68.7% | 65.4% | 2.3% | 97.7% | 31.6% | 6.6% | — | 37.74s |
| 7 | deepseek-v4-pro | 65.3% | 65.2% | 0.0% | 100.0% | 31.6% | 5.3% | — | 36.63s |
| 8 | deepseek-v4-flash | 63.7% | 62.3% | 0.0% | 100.0% | 31.6% | 9.2% | $0.10 | 25.47s |
| 9 | grok-4.1-fast | 62.3% | 53.2% | 9.1% | 90.9% | 31.6% | 11.8% | — | 11.01s |
| 10 | kimi-k2.6 | 63.8% | 63.2% | 0.0% | 100.0% | 32.9% | 3.9% | — | 63.32s |
| 11 | grok-4-openrouter | 62.4% | 55.7% | 6.8% | 93.2% | 32.9% | 10.5% | — | 24.82s |
| 12 | grok-4-fast | 60.5% | 51.5% | 6.8% | 93.2% | 32.9% | 9.2% | — | 9.87s |
| 13 | glm-5.1 | 67.3% | 66.1% | 0.0% | 100.0% | 34.2% | 7.9% | — | 43.93s |
| 14 | glm-5 | 64.7% | 64.7% | 0.0% | 100.0% | 34.2% | 7.9% | — | 38.18s |
| 15 | claude-opus-4.5 | 63.5% | 60.8% | 2.3% | 97.7% | 34.2% | 10.5% | — | 9.80s |
| 16 | claude-haiku-4.5 | 58.1% | 48.2% | 6.8% | 93.2% | 34.2% | 9.2% | — | 5.89s |
| 17 | gemma4-31b | 66.4% | 66.2% | 0.0% | 100.0% | 36.8% | 7.9% | $0.00 | 16.86s |
| 18 | gemini-3.1-pro | 67.1% | 63.8% | 2.3% | 97.7% | 36.8% | 3.9% | — | 24.97s |
| 19 | minimax-m2.7 | 57.9% | 60.6% | 2.3% | 97.7% | 36.8% | 2.6% | — | 21.26s |
| 20 | qwen3.5-9b | 55.8% | 50.3% | 11.4% | 88.6% | 36.8% | 2.6% | — | 23.02s |
| 21 | gemini-2.5-pro | 60.4% | 59.7% | 0.0% | 100.0% | 38.2% | 21.1% | — | 15.82s |
| 22 | grok-4.3 | 60.5% | 61.3% | 2.3% | 97.7% | 39.5% | 7.9% | — | 17.10s |
| 23 | grok-4.20 | 59.6% | 58.6% | 4.5% | 95.5% | 39.5% | 1.3% | $2.23 | 9.46s |
| 24 | ring-2.6-1t | 61.3% | 58.2% | 6.8% | 93.2% | 39.5% | 7.9% | — | 40.47s |
| 25 | gpt-5.5 | 58.4% | 64.6% | 0.0% | 100.0% | 40.8% | 6.6% | — | 55.85s |
| 26 | claude-sonnet-4.5 | 61.6% | 61.8% | 0.0% | 100.0% | 42.1% | 9.2% | — | 10.49s |
| 27 | claude-opus-4.6 | 61.3% | 59.7% | 0.0% | 100.0% | 42.1% | 9.2% | — | 11.52s |
| 28 | qwen35-397b | 57.6% | 61.9% | 0.0% | 100.0% | 43.4% | 2.6% | — | 46.97s |
| 29 | gpt-5 | 55.5% | 59.6% | 0.0% | 100.0% | 44.7% | 5.3% | — | 28.34s |
| 30 | nemotron-3-super-120b | 53.7% | 57.0% | 0.0% | 100.0% | 44.7% | 6.6% | — | 43.50s |
| 31 | minimax-m2.5 | 53.2% | 54.7% | 0.0% | 100.0% | 44.7% | 0.0% | $0.16 | 19.88s |
| 32 | gpt-5.4 | 49.9% | 55.8% | 0.0% | 100.0% | 46.1% | 0.0% | — | 7.39s |
| 33 | gpt-5.4-mini | 52.5% | 50.1% | 6.8% | 93.2% | 46.1% | 5.3% | — | 4.44s |
| 34 | deepseek-v3.1 | 54.4% | 57.4% | 0.0% | 100.0% | 48.7% | 7.9% | — | 18.42s |
| 35 | qwen3-235b-a22b | 61.1% | 68.4% | 0.0% | 100.0% | 50.0% | 3.9% | $0.00 | 31.93s |
| 36 | claude-sonnet-4.6 | 57.3% | 59.6% | 0.0% | 100.0% | 50.0% | 9.2% | — | 12.15s |
| 37 | gemini-2.5-flash | 52.0% | 51.0% | 2.3% | 97.7% | 51.3% | 15.8% | — | 3.07s |
| 38 | deepseek-v3.2 | 55.4% | 60.1% | 0.0% | 100.0% | 52.6% | 10.5% | $0.32 | 73.10s |

**Matched:** 38 / 47 complete models.

**Interpretation:** Under these constraints, `qwen3.6-max` is the current review-load reduction leader by False Review Load. `gemini-3.1-flash-lite` is the stronger overall option, but ranks fourth here because this profile sorts primarily by review-load reduction.

## Generated CSVs

- [combined/operational-baselines.csv](combined/operational-baselines.csv)
- [combined/operational-profile-high-safety.csv](combined/operational-profile-high-safety.csv)
- [combined/operational-profile-balanced-soc.csv](combined/operational-profile-balanced-soc.csv)
- [combined/operational-profile-noise-reduction.csv](combined/operational-profile-noise-reduction.csv)
