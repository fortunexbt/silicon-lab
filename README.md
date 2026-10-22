# silicon-lab

A small Python package and CLI for comparing two configurations on one machine without fooling yourself. It extracts the method shared by four earlier benchmarking projects: matched pairs, order balanced as A-B-B-A, warm-up discarded, raw JSON kept, and a bootstrap interval on the paired difference.

## Method

1. **A-B-B-A blocks.** Each block runs A, B, B, A. A linear drift in the machine (thermals, caches, background load) hits both arms equally and cancels in the block difference.
2. **Warm-up discard.** Each run makes some warm-up calls first. Their values are kept in the raw record but excluded from the statistics.
3. **Run value.** A run's value is the median of its measured trials.
4. **Paired difference.** Per block, B mean minus A mean.
5. **Interval.** A seeded percentile bootstrap of the mean over block differences (10,000 resamples, seed 20261023, 95%). With fewer than two blocks there is no interval and the report says so.
6. **Environment.** Every record stores chip, OS, Python, CPU count, memory and power source.

## Install and use

```
pip install -e ".[dev]"

silicon-lab run --blocks 6 --label "hash chain 20k vs 40k" --out result.json \
    --hash-rounds 20000 40000
silicon-lab report result.json --out REPORT.md
```

Time your own commands with `--cmd-a "..." --cmd-b "..."` instead of `--hash-rounds`. Run `silicon-lab run --help` for all options. The test suite uses a deterministic CPU hash loop as its workload and never runs a model.

## Reports

Three earlier measurements, re-expressed with their raw data, pinned recipes, and the time and place they ran. Each `build.py` regenerates its `REPORT.md` from the committed data, and CI checks the output is unchanged. This repository did not rerun any of these measurements.

| Report | Headline | Interval | Main limit |
|---|---|---|---|
| [flock](reports/flock/REPORT.md) | Candidate 4.95% slower than base (0.5448 s vs 0.5191 s), A-B-B-A on one CI VM, 2026-09 | none, one block | mixed-hardware runner pool; a diagnostic, not a score |
| [qwen38](reports/qwen38/REPORT.md) | 42.13 tok/s median decode, five prompts, 24 GB M4, 2026-10-19 | none, not a paired design | prompts range 24.18 to 46.21 tok/s; sweep rows are single measurements |
| [shader](reports/shader/REPORT.md) | repeat noise of one shader profile on a base M4, plus six matched pairs | n=3 bootstrap on the repeats | one machine, a CPU frame metric, one capture per pair arm |

## Sources and licences

- `minecraft-apple-silicon-framework` (shader captures and ledger): MIT.
- Flock baseline runner (CI log of one run): the project's own repository.
- Local MLX/llama.cpp optimisation notes (qwen38): only throughput numbers are published. The model's licence was not verified, so no weights or outputs are included.

This repository is MIT licensed.
