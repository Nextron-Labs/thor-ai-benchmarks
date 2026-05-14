# Operational Profiles — Extended Tables

This file is generated from the current public CSV artifacts. The main summary lives in [README.md](README.md).

## Baseline Reference

| # | Model | CW% | BalOTS | CritMiss | ThreatCap | FalseRev | FalseEsc | Cost/Run | AvgTime |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | always-fp | 26.6% | -58.3% | 100.0% | 0.0% | 0.0% | 0.0% | 0.00 | 0.00s |
| 2 | always-inc | 25.5% | 38.3% | 0.0% | 100.0% | 100.0% | 0.0% | 0.00 | 0.00s |
| 3 | always-tp | 17.9% | 25.0% | 0.0% | 100.0% | 100.0% | 100.0% | 0.00 | 0.00s |

Baselines are references, not recommendations. `always-fp` suppresses everything and is dangerous; `always-inc` sends everything to review and is safe but operationally weak; `always-tp` escalates everything and is noisy.

## Profile 1: High-Safety

**Use case:** Environments where missing any real incident is unacceptable.

**Requirements:** Complete coverage, Critical Miss Rate ≤ 5%, Threat Capture Rate ≥ 95%, False Review Load ≤ 75%.

**Ranking:** Balanced OTS descending, then False Review Load ascending.

| # | Model | CW% | BalOTS | CritMiss | ThreatCap | FalseRev | FalseEsc | Cost/Run | AvgTime |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | gemini-3.1-flash-lite | 69.4% | 71.6% | 0.0% | 100.0% | 28.1% | 1.1% | — | 2.08s |
| 2 | gemma4-31b | 66.5% | 67.2% | 0.0% | 100.0% | 34.8% | 6.7% | 0.00 | 15.65s |
| 3 | qwen3-235b-a22b | 58.7% | 65.6% | 0.0% | 100.0% | 50.6% | 5.6% | 0.00 | 29.82s |
| 4 | glm-5.1 | 66.1% | 65.4% | 1.8% | 98.2% | 32.6% | 6.7% | — | 41.68s |
| 5 | gpt-5.5 | 59.3% | 64.0% | 0.0% | 100.0% | 40.4% | 5.6% | — | 62.11s |
| 6 | glm-5 | 63.4% | 63.8% | 1.8% | 98.2% | 34.8% | 7.9% | — | 38.46s |
| 7 | gemini-3.1-pro | 65.5% | 63.3% | 1.8% | 98.2% | 36.0% | 3.4% | — | 22.53s |
| 8 | claude-opus-4.5 | 63.7% | 62.9% | 1.8% | 98.2% | 34.8% | 10.1% | — | 9.68s |
| 9 | deepseek-v4-pro | 64.0% | 61.9% | 1.8% | 98.2% | 30.3% | 4.5% | — | 36.07s |
| 10 | kimi-k2.6 | 63.7% | 61.3% | 3.6% | 96.4% | 31.5% | 3.4% | — | 60.73s |
| 11 | qwen35-397b | 57.1% | 61.2% | 0.0% | 100.0% | 43.8% | 2.2% | — | 45.17s |
| 12 | deepseek-v4-flash | 63.3% | 59.9% | 3.6% | 96.4% | 30.3% | 7.9% | 0.10 | 27.89s |
| 13 | claude-opus-4.6 | 60.4% | 59.8% | 0.0% | 100.0% | 43.8% | 9.0% | — | 11.49s |
| 14 | deepseek-v3.2 | 55.0% | 59.8% | 0.0% | 100.0% | 51.7% | 10.1% | 0.32 | 69.70s |
| 15 | grok-4.3 | 60.3% | 59.7% | 3.6% | 96.4% | 38.2% | 7.9% | — | 16.59s |
| 16 | deepseek-v3.1 | 55.8% | 59.5% | 0.0% | 100.0% | 48.3% | 7.9% | — | 18.87s |
| 17 | gemini-2.5-pro | 59.8% | 59.1% | 1.8% | 98.2% | 38.2% | 21.3% | — | 15.90s |
| 18 | claude-sonnet-4.5 | 58.1% | 58.6% | 1.8% | 98.2% | 43.8% | 11.2% | — | 11.72s |
| 19 | nemotron-3-super-120b | 53.7% | 58.3% | 0.0% | 100.0% | 44.9% | 5.6% | — | 39.30s |
| 20 | gpt-5 | 54.7% | 58.2% | 0.0% | 100.0% | 43.8% | 4.5% | — | 27.77s |
| 21 | claude-sonnet-4.6 | 55.9% | 58.2% | 0.0% | 100.0% | 49.4% | 7.9% | — | 12.08s |
| 22 | minimax-m2.7 | 55.0% | 56.4% | 3.6% | 96.4% | 39.3% | 2.2% | — | 20.44s |
| 23 | gpt-5-mini | 48.6% | 56.0% | 0.0% | 100.0% | 66.3% | 5.6% | — | 21.28s |
| 24 | llama-3.1-70b | 52.0% | 55.5% | 1.8% | 98.2% | 56.2% | 29.2% | 0.00 | 13.96s |
| 25 | gpt-5.4 | 49.8% | 54.6% | 1.8% | 98.2% | 44.9% | 0.0% | — | 7.47s |
| 26 | gemini-2.5-flash | 53.3% | 53.7% | 1.8% | 98.2% | 50.6% | 15.7% | — | 3.04s |
| 27 | minimax-m2.5 | 51.7% | 51.5% | 0.0% | 100.0% | 46.1% | 0.0% | 0.16 | 18.27s |
| 28 | mercury-2 | 44.7% | 45.3% | 3.6% | 96.4% | 56.2% | 5.6% | — | 1.67s |

**Matched:** 28 / 46 complete models.

**Interpretation:** Under these constraints, `gemini-3.1-flash-lite` is the current profile leader. Values are generated from `combined/operational-profile-high-safety.csv`.

## Profile 2: Balanced SOC

**Use case:** General SOC operations where a balance between safety and efficiency is needed.

**Requirements:** Complete coverage, Critical Miss Rate ≤ 15%, Threat Capture Rate ≥ 85%, False Review Load ≤ 75%.

**Ranking:** Balanced OTS descending.

| # | Model | CW% | BalOTS | CritMiss | ThreatCap | FalseRev | FalseEsc | Cost/Run | AvgTime |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | gemini-3.1-flash-lite | 69.4% | 71.6% | 0.0% | 100.0% | 28.1% | 1.1% | — | 2.08s |
| 2 | gemma4-31b | 66.5% | 67.2% | 0.0% | 100.0% | 34.8% | 6.7% | 0.00 | 15.65s |
| 3 | qwen3-235b-a22b | 58.7% | 65.6% | 0.0% | 100.0% | 50.6% | 5.6% | 0.00 | 29.82s |
| 4 | glm-5.1 | 66.1% | 65.4% | 1.8% | 98.2% | 32.6% | 6.7% | — | 41.68s |
| 5 | gpt-5.5 | 59.3% | 64.0% | 0.0% | 100.0% | 40.4% | 5.6% | — | 62.11s |
| 6 | glm-5 | 63.4% | 63.8% | 1.8% | 98.2% | 34.8% | 7.9% | — | 38.46s |
| 7 | gemini-3.1-pro | 65.5% | 63.3% | 1.8% | 98.2% | 36.0% | 3.4% | — | 22.53s |
| 8 | claude-opus-4.5 | 63.7% | 62.9% | 1.8% | 98.2% | 34.8% | 10.1% | — | 9.68s |
| 9 | kimi-k2.5 | 66.9% | 62.1% | 5.5% | 94.5% | 32.6% | 5.6% | — | 42.18s |
| 10 | deepseek-v4-pro | 64.0% | 61.9% | 1.8% | 98.2% | 30.3% | 4.5% | — | 36.07s |
| 11 | kimi-k2.6 | 63.7% | 61.3% | 3.6% | 96.4% | 31.5% | 3.4% | — | 60.73s |
| 12 | qwen35-397b | 57.1% | 61.2% | 0.0% | 100.0% | 43.8% | 2.2% | — | 45.17s |
| 13 | deepseek-v4-flash | 63.3% | 59.9% | 3.6% | 96.4% | 30.3% | 7.9% | 0.10 | 27.89s |
| 14 | claude-opus-4.6 | 60.4% | 59.8% | 0.0% | 100.0% | 43.8% | 9.0% | — | 11.49s |
| 15 | deepseek-v3.2 | 55.0% | 59.8% | 0.0% | 100.0% | 51.7% | 10.1% | 0.32 | 69.70s |
| 16 | grok-4.3 | 60.3% | 59.7% | 3.6% | 96.4% | 38.2% | 7.9% | — | 16.59s |
| 17 | deepseek-v3.1 | 55.8% | 59.5% | 0.0% | 100.0% | 48.3% | 7.9% | — | 18.87s |
| 18 | gemini-2.5-pro | 59.8% | 59.1% | 1.8% | 98.2% | 38.2% | 21.3% | — | 15.90s |
| 19 | claude-sonnet-4.5 | 58.1% | 58.6% | 1.8% | 98.2% | 43.8% | 11.2% | — | 11.72s |
| 20 | nemotron-3-super-120b | 53.7% | 58.3% | 0.0% | 100.0% | 44.9% | 5.6% | — | 39.30s |
| 21 | gpt-5 | 54.7% | 58.2% | 0.0% | 100.0% | 43.8% | 4.5% | — | 27.77s |
| 22 | claude-sonnet-4.6 | 55.9% | 58.2% | 0.0% | 100.0% | 49.4% | 7.9% | — | 12.08s |
| 23 | grok-4-openrouter | 61.7% | 56.4% | 7.3% | 92.7% | 32.6% | 10.1% | — | 22.87s |
| 24 | minimax-m2.7 | 55.0% | 56.4% | 3.6% | 96.4% | 39.3% | 2.2% | — | 20.44s |
| 25 | gpt-5-mini | 48.6% | 56.0% | 0.0% | 100.0% | 66.3% | 5.6% | — | 21.28s |
| 26 | llama-3.1-70b | 52.0% | 55.5% | 1.8% | 98.2% | 56.2% | 29.2% | 0.00 | 13.96s |
| 27 | grok-4.20 | 57.4% | 54.7% | 7.3% | 92.7% | 39.3% | 1.1% | 2.23 | 8.53s |
| 28 | gpt-5.4 | 49.8% | 54.6% | 1.8% | 98.2% | 44.9% | 0.0% | — | 7.47s |
| 29 | gemini-2.5-flash | 53.3% | 53.7% | 1.8% | 98.2% | 50.6% | 15.7% | — | 3.04s |
| 30 | minimax-m2.5 | 51.7% | 51.5% | 0.0% | 100.0% | 46.1% | 0.0% | 0.16 | 18.27s |
| 31 | grok-4.1-fast | 59.9% | 51.2% | 10.9% | 89.1% | 33.7% | 13.5% | — | 9.85s |
| 32 | qwen3.5-plus-20260420 | 62.5% | 50.4% | 10.9% | 89.1% | 20.2% | 5.6% | — | 44.66s |
| 33 | devstral-small | 46.8% | 49.5% | 5.5% | 94.5% | 68.5% | 11.2% | — | 1.54s |
| 34 | mimo-v2-pro | 59.9% | 49.2% | 7.3% | 92.7% | 27.0% | 12.4% | — | 10.01s |
| 35 | grok-4-fast | 58.4% | 49.2% | 9.1% | 90.9% | 34.8% | 11.2% | — | 9.01s |
| 36 | qwen3.5-9b | 54.4% | 47.9% | 12.7% | 87.3% | 34.8% | 2.2% | — | 23.11s |
| 37 | gpt-5.4-mini | 51.2% | 47.2% | 10.9% | 89.1% | 44.9% | 4.5% | — | 4.21s |
| 38 | qwen3.6-plus | 59.4% | 45.5% | 12.7% | 87.3% | 24.7% | 3.4% | — | 41.29s |
| 39 | mercury-2 | 44.7% | 45.3% | 3.6% | 96.4% | 56.2% | 5.6% | — | 1.67s |
| 40 | claude-haiku-4.5 | 54.8% | 42.4% | 12.7% | 87.3% | 33.7% | 9.0% | — | 5.93s |
| 41 | mistral-nemo | 39.8% | 34.7% | 9.1% | 90.9% | 62.9% | 18.0% | — | 5.73s |

**Matched:** 41 / 46 complete models.

**Interpretation:** Under these constraints, `gemini-3.1-flash-lite` is the current profile leader. Values are generated from `combined/operational-profile-balanced-soc.csv`.

## Profile 3: Noise-Reduction

**Use case:** High-volume alert triage where reducing review load is a priority and some miss risk is acceptable.

**Requirements:** Complete coverage, False Review Load ≤ 55%, Critical Miss Rate ≤ 20%, Balanced OTS > 0.

**Ranking:** False Review Load ascending, then Balanced OTS descending.

| # | Model | CW% | BalOTS | CritMiss | ThreatCap | FalseRev | FalseEsc | Cost/Run | AvgTime |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | qwen3.5-plus-20260420 | 62.5% | 50.4% | 10.9% | 89.1% | 20.2% | 5.6% | — | 44.66s |
| 2 | qwen3.6-max | 62.9% | 44.6% | 16.4% | 83.6% | 20.2% | 6.7% | — | 95.74s |
| 3 | qwen3.6-plus | 59.4% | 45.5% | 12.7% | 87.3% | 24.7% | 3.4% | — | 41.29s |
| 4 | mimo-v2-pro | 59.9% | 49.2% | 7.3% | 92.7% | 27.0% | 12.4% | — | 10.01s |
| 5 | gemini-3.1-flash-lite | 69.4% | 71.6% | 0.0% | 100.0% | 28.1% | 1.1% | — | 2.08s |
| 6 | deepseek-v4-pro | 64.0% | 61.9% | 1.8% | 98.2% | 30.3% | 4.5% | — | 36.07s |
| 7 | deepseek-v4-flash | 63.3% | 59.9% | 3.6% | 96.4% | 30.3% | 7.9% | 0.10 | 27.89s |
| 8 | kimi-k2.6 | 63.7% | 61.3% | 3.6% | 96.4% | 31.5% | 3.4% | — | 60.73s |
| 9 | glm-5.1 | 66.1% | 65.4% | 1.8% | 98.2% | 32.6% | 6.7% | — | 41.68s |
| 10 | kimi-k2.5 | 66.9% | 62.1% | 5.5% | 94.5% | 32.6% | 5.6% | — | 42.18s |
| 11 | grok-4-openrouter | 61.7% | 56.4% | 7.3% | 92.7% | 32.6% | 10.1% | — | 22.87s |
| 12 | grok-4.1-fast | 59.9% | 51.2% | 10.9% | 89.1% | 33.7% | 13.5% | — | 9.85s |
| 13 | claude-haiku-4.5 | 54.8% | 42.4% | 12.7% | 87.3% | 33.7% | 9.0% | — | 5.93s |
| 14 | gemma4-31b | 66.5% | 67.2% | 0.0% | 100.0% | 34.8% | 6.7% | 0.00 | 15.65s |
| 15 | glm-5 | 63.4% | 63.8% | 1.8% | 98.2% | 34.8% | 7.9% | — | 38.46s |
| 16 | claude-opus-4.5 | 63.7% | 62.9% | 1.8% | 98.2% | 34.8% | 10.1% | — | 9.68s |
| 17 | grok-4-fast | 58.4% | 49.2% | 9.1% | 90.9% | 34.8% | 11.2% | — | 9.01s |
| 18 | qwen3.5-9b | 54.4% | 47.9% | 12.7% | 87.3% | 34.8% | 2.2% | — | 23.11s |
| 19 | gemini-3.1-pro | 65.5% | 63.3% | 1.8% | 98.2% | 36.0% | 3.4% | — | 22.53s |
| 20 | grok-4.3 | 60.3% | 59.7% | 3.6% | 96.4% | 38.2% | 7.9% | — | 16.59s |
| 21 | gemini-2.5-pro | 59.8% | 59.1% | 1.8% | 98.2% | 38.2% | 21.3% | — | 15.90s |
| 22 | minimax-m2.7 | 55.0% | 56.4% | 3.6% | 96.4% | 39.3% | 2.2% | — | 20.44s |
| 23 | grok-4.20 | 57.4% | 54.7% | 7.3% | 92.7% | 39.3% | 1.1% | 2.23 | 8.53s |
| 24 | gpt-5.5 | 59.3% | 64.0% | 0.0% | 100.0% | 40.4% | 5.6% | — | 62.11s |
| 25 | qwen35-397b | 57.1% | 61.2% | 0.0% | 100.0% | 43.8% | 2.2% | — | 45.17s |
| 26 | claude-opus-4.6 | 60.4% | 59.8% | 0.0% | 100.0% | 43.8% | 9.0% | — | 11.49s |
| 27 | claude-sonnet-4.5 | 58.1% | 58.6% | 1.8% | 98.2% | 43.8% | 11.2% | — | 11.72s |
| 28 | gpt-5 | 54.7% | 58.2% | 0.0% | 100.0% | 43.8% | 4.5% | — | 27.77s |
| 29 | nemotron-3-super-120b | 53.7% | 58.3% | 0.0% | 100.0% | 44.9% | 5.6% | — | 39.30s |
| 30 | gpt-5.4 | 49.8% | 54.6% | 1.8% | 98.2% | 44.9% | 0.0% | — | 7.47s |
| 31 | gpt-5.4-mini | 51.2% | 47.2% | 10.9% | 89.1% | 44.9% | 4.5% | — | 4.21s |
| 32 | minimax-m2.5 | 51.7% | 51.5% | 0.0% | 100.0% | 46.1% | 0.0% | 0.16 | 18.27s |
| 33 | deepseek-v3.1 | 55.8% | 59.5% | 0.0% | 100.0% | 48.3% | 7.9% | — | 18.87s |
| 34 | claude-sonnet-4.6 | 55.9% | 58.2% | 0.0% | 100.0% | 49.4% | 7.9% | — | 12.08s |
| 35 | qwen3-235b-a22b | 58.7% | 65.6% | 0.0% | 100.0% | 50.6% | 5.6% | 0.00 | 29.82s |
| 36 | gemini-2.5-flash | 53.3% | 53.7% | 1.8% | 98.2% | 50.6% | 15.7% | — | 3.04s |
| 37 | deepseek-v3.2 | 55.0% | 59.8% | 0.0% | 100.0% | 51.7% | 10.1% | 0.32 | 69.70s |

**Matched:** 37 / 46 complete models.

**Interpretation:** Under these constraints, `qwen3.5-plus-20260420` is the current profile leader. Values are generated from `combined/operational-profile-noise-reduction.csv`.

## Generated CSVs

- [combined/operational-baselines.csv](combined/operational-baselines.csv)
- [combined/operational-profile-high-safety.csv](combined/operational-profile-high-safety.csv)
- [combined/operational-profile-balanced-soc.csv](combined/operational-profile-balanced-soc.csv)
- [combined/operational-profile-noise-reduction.csv](combined/operational-profile-noise-reduction.csv)
