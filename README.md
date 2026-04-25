# THOR AI Benchmarks

> Benchmarking LLM models on THOR finding triage quality against human expert ground truth.

This repository contains the public benchmark results. The scoring methodology, ground truth data, and scoring scripts remain in a private repository to prevent gaming.

## Latest Results (R1+R2+R3 Combined, 21 models)

### CW% Leaderboard (Confidence-Weighted Score)

Higher is better. Rewards confident correct answers, punishes confident wrong answers.

![CW% Leaderboard](charts/cw-leaderboard.png)

### CW% vs MAE

Top-right = best (high CW%, low MAE).

![CW% vs MAE](charts/cw-vs-mae.png)

### Classification Accuracy Breakdown

Green = exact match, orange = one step off (e.g., TP↔Inc), red = two steps off (e.g., TP↔FP).

![Classification Breakdown](charts/classification-breakdown.png)

## Full Data

See [combined/leaderboard.csv](combined/leaderboard.csv) for the complete sortable data.

## Methodology

See [ground-truth/methodology.json](ground-truth/methodology.json) for scoring definitions.

### Key Terms

| Abbreviation | Meaning |
|---|---|
| **CW%** | Confidence-Weighted Score — primary ranking metric |
| **Ord%** | Ordinal Accuracy — simple exact/near/miss scoring |
| **MAE** | Mean Absolute Error — average |AI score − Human score| |
| **RMSE** | Root Mean Square Error — penalizes large errors |
| **TP** | True Positive — genuine security finding |
| **Inc** | Inconclusive — cannot definitively classify |
| **FP** | False Positive — not a genuine security finding |
| **Ex** | Exact classification matches |
| **Mi** | Minor misses (one category off) |
| **Ha** | Hard misses (two categories off) |

### CW Formula

| AI vs Ground Truth | CW Points |
|---|---|
| Exact match | +1.0 + confidence/100 |
| One step off (e.g., TP↔Inc) | +1.0 − confidence/100 |
| Two steps off (e.g., TP↔FP) | −confidence/100 |

Maximum per finding: 2.0 (exact match at 100% confidence).

## Related

- **Mjolnir AI** — [github.com/Nextron-Labs/mjolnir-ai](https://github.com/Nextron-Labs/mjolnir-ai) — the AI triage tool
- **THOR** — [nextron-systems.com/thor](https://nextron-systems.com/thor/) — the forensic scanner

## License

Benchmark results © Nextron Systems.