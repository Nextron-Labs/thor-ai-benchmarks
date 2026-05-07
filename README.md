# THOR AI Benchmarks

> Benchmarking LLM models on THOR finding triage quality against human expert ground truth.

This repository contains public benchmark results for evaluating how well LLMs can triage THOR security findings.

The benchmark is built for a specific use case: security event and forensic finding assessment. It is not a general LLM benchmark, not a coding benchmark, and not a vulnerability research benchmark.

The goal is to answer a more practical question:

> Given the same enriched THOR finding, how well can a model assess whether it is a true positive, false positive, or inconclusive, and how close is its priority score to a human expert assessment?

The benchmark compares models against human expert ground truth. The public repository contains the methodology, charts and aggregated result data. The exact finding set, ground truth data and scoring scripts remain private.

There are two main reasons for that:

1. Once benchmark data is public, it can end up in future training data through normal web crawling. That does not require anyone to intentionally train against this benchmark. Public data just has a way of becoming training data sooner or later.
2. Some reports behind the findings are based on real investigations, not only synthetic lab data. We do not publish that material unless we are completely sure that everything is properly cleaned and anonymized.

## Benchmark Setup

Each model receives the same THOR finding context and has to return a structured assessment.

The model is asked to provide:

- A classification: `TP`, `FP`, or `Inconclusive`
- A priority score
- A confidence value
- A short reasoning / assessment

The benchmark intentionally evaluates the model's direct triage ability based on the provided THOR finding. It does not give models access to external tools during the run.

No additional lookup is performed during scoring:

- No VirusTotal lookup
- No sandbox query
- No SIEM search
- No EDR artifact retrieval
- No ITAM / CMDB lookup
- No private knowledge base retrieval
- No additional internet search

This is intentional.

Once external tools are added, the benchmark no longer measures only the model's triage ability. It starts measuring a combined system: model, prompt, tool selection, tool quality, available data, integration design and environment-specific context.

That may be closer to a production SOC workflow, but it is much harder to compare fairly. Every organization has a different tool stack. There is no realistic "average SOC toolset" that would make such a benchmark generally meaningful.

Tool use can absolutely improve results in practice, especially for weaker models. A model with access to VT, SIEM context, EDR telemetry, asset data or sandbox results may classify some findings better than a model without those inputs.

But in that case, the result depends heavily on the tools and the quality of their data.

For THOR findings, a lot of enrichment is already part of the event itself. THOR tries to attach as much useful context as possible to a finding: hashes, owners, timestamps, file headers, metadata and other attributes that may not exist in the original artifact source. For example, a ShimCache entry may only contain a file path, SHA1 and timestamp at first, but THOR can enrich it with additional file and metadata context.

So this benchmark measures how well models interpret the enriched THOR finding itself.

If you test the same models in your own workflow, the results may differ slightly or substantially. That depends on the prompt, the surrounding instructions, the available tools, the quality of external data and how well the model can use those tools. Once you move from this controlled setup to an agentic workflow, you are no longer testing the same thing.

In that sense, this benchmark should be read as a baseline, not as a ceiling. It is closer to measuring how well a model performs on a standardized exam without external aids than how well it performs inside a fully equipped production workflow.

For this benchmark, final truth comes from human expert ground truth, not from an LLM judge. Judge models can be useful in workflow-specific evaluation harnesses, but they are not used here as the authority that decides which model was actually closer to the truth.
