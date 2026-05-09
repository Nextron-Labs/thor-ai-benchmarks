# Operational Profiles — Extended Tables

This is the extended operational profile reference for the THOR AI benchmark. The main summary now lives in [README.md](README.md); this page is kept for quick access to the profile constraints and generated tables.

## Baseline Reference

| Strategy | CW% | BalOTS | CritMiss | ThreatCap | FalseRev | FalseEsc | Cost/Run |
|---|---:|---:|---:|---:|---:|---:|---:|
| always-fp | 26.9% | -58.3% | 100.0% | 0.0% | 0.0% | 0.0% | $0.00 |
| always-inc | 22.1% | 38.3% | 0.0% | 100.0% | 100.0% | 0.0% | $0.00 |
| always-tp | 19.2% | 25.0% | 0.0% | 100.0% | 100.0% | 100.0% | $0.00 |

Baselines are references, not recommendations. `always-fp` suppresses everything and is dangerous; `always-inc` sends everything to review and is safe but operationally weak; `always-tp` escalates everything and is noisy.

## Profile 1: High-Safety

**Use case:** Environments where missing any real incident is unacceptable.

**Requirements:** Critical Miss Rate ≤ 5%, Threat Capture Rate ≥ 95%, False Review Load < 100%.

**Ranking:** Balanced OTS descending, then False Review Load ascending.

| # | Model | CW% | BalOTS | CritMiss | ThreatCap | FalseRev | FalseEsc | Cost/Run | AvgTime |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | llama-3.1-8b | 28.0% | 40.0% | 2.1% | 97.9% | 88.2% | 6.6% | $0.00 | 12.65s |
| 2 | gpt-5-nano | 27.7% | 35.9% | 2.1% | 97.9% | 90.8% | 18.4% | $0.12 | 31.26s |

**Matched:** 2 / 48 models.

**Interpretation:** Under these constraints, `llama-3.1-8b` is the current profile leader. It beats `always-inc` on Balanced OTS while maintaining near-zero critical miss rate, but it still leaves high review load.

## Profile 2: Balanced SOC

**Use case:** General SOC operations where a balance between safety and efficiency is needed.

**Requirements:** Critical Miss Rate ≤ 15%, Threat Capture Rate ≥ 85%, False Review Load ≤ 75%.

**Ranking:** Balanced OTS descending.

| # | Model | CW% | BalOTS | CritMiss | ThreatCap | FalseRev | FalseEsc | Cost/Run | AvgTime |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | deepseek-v3.2 | 38.8% | 37.4% | 14.6% | 85.4% | 61.8% | 14.5% | $0.32 | 73.28s |
| 2 | nemotron-3-nano-omni | 35.2% | 33.1% | 14.6% | 85.4% | 69.3% | 18.7% | $0.00 | 47.19s |
| 3 | llama-3.1-70b | 36.9% | 30.5% | 14.6% | 85.4% | 67.1% | 31.6% | $0.00 | 13.93s |
| 4 | qwen3-235b-a22b | 33.0% | 26.8% | 12.5% | 87.5% | 65.8% | 14.5% | $0.00 | 32.24s |
| 5 | minimax-m2.5 | 32.9% | 22.0% | 14.6% | 85.4% | 59.2% | 10.5% | $0.16 | 20.07s |
| 6 | gpt-oss-120b | 31.3% | 21.6% | 12.8% | 87.2% | 66.7% | 4.2% | $0.00 | 16.80s |

**Matched:** 6 / 48 models.

**Interpretation:** Under these constraints, `deepseek-v3.2` currently provides the best balance in this data set. It nearly matches `always-inc` on Balanced OTS while reducing review load by about 38 percentage points.

## Profile 3: Noise-Reduction

**Use case:** High-volume alert triage where reducing review load is a priority and some miss risk is acceptable.

**Requirements:** False Review Load ≤ 55%, Critical Miss Rate ≤ 20%, Balanced OTS > 0.

**Ranking:** False Review Load ascending, then Balanced OTS descending.

| # | Model | CW% | BalOTS | CritMiss | ThreatCap | FalseRev | FalseEsc | Cost/Run | AvgTime |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | deepseek-v4-flash | 40.9% | 26.2% | 16.7% | 83.3% | 48.7% | 19.7% | $0.10 | 24.31s |
| 2 | gemma4-31b | 40.6% | 27.1% | 18.8% | 81.2% | 52.6% | 13.2% | $0.00 | 17.21s |
| 3 | grok-4.20 | 36.0% | 22.9% | 18.8% | 81.2% | 52.6% | 9.2% | $2.23 | 9.39s |

**Matched:** 3 / 48 models.

**Interpretation:** Under these constraints, `deepseek-v4-flash` is the current review-load reduction leader. It reduces review load substantially compared with `always-inc`, but its miss risk is too high for high-safety use cases.

## Generated CSVs

- [combined/operational-baselines.csv](combined/operational-baselines.csv)
- [combined/operational-profile-high-safety.csv](combined/operational-profile-high-safety.csv)
- [combined/operational-profile-balanced-soc.csv](combined/operational-profile-balanced-soc.csv)
- [combined/operational-profile-noise-reduction.csv](combined/operational-profile-noise-reduction.csv)
