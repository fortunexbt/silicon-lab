# Flock aligned recycling: base (A) vs candidate (B), A-B-B-A on one CI VM

## Result

- A mean: 0.5191 s
- B mean: 0.5448 s
- Paired difference (B - A): **+0.02569 s** (+4.95%)
- 95% bootstrap CI: n/a
- Blocks: 1 (A-B-B-A each); 10000 resamples, seed 20261023
- Not enough blocks for an interval; treat the difference as a single observation.

## Blocks

| Block | A mean (s) | B mean (s) | B - A (s) |
|---:|---:|---:|---:|
| 0 | 0.5191 | 0.5448 | +0.02569 |

## Runs

| Block | Pos | Arm | Warm-up discarded (s) | Trials (s) | Run value (s) |
|---:|---:|:--:|---|---|---:|
| 0 | 0 | A | 0.4973 | 0.5287, 0.6677, 0.4958 | 0.5287 |
| 0 | 1 | B | 0.4839 | 0.5224, 0.8804, 0.551 | 0.551 |
| 0 | 2 | B | 0.4992 | 0.8781, 0.5062, 0.5385 | 0.5385 |
| 0 | 3 | A | 0.4968 | 0.5094, 0.5057, 0.554 | 0.5094 |

## Environment

- chip: AMD EPYC 9V45 96-Core Processor (4 threads used)
- os: GitHub-hosted ubuntu-24.04, image 20260907.300.1
- time: 2026-09-17/18 (GitHub Actions run 35289110576)

## Method

Runs follow A-B-B-A within each block, so linear drift cancels in the block difference. Warm-up calls are discarded but kept in the raw record. A run's value is the median of its trials. The interval is a seeded percentile bootstrap of the mean over block differences; with fewer than two blocks it is not defined.

## Headline

Candidate is 4.95% slower than base on this VM (0.5448 s against 0.5191 s per verified batch), from one block with no interval. Read it as a diagnostic, not a verdict.

## Limits

- One A-B-B-A block on one VM, so there is no confidence interval. This is a single
  observation, not an estimate of spread.
- GitHub-hosted runners are a mixed-hardware pool. The workflow itself labels the result
  "same-VM diagnostic A-B-B-A; not an official ranked score". Compare nothing here with a
  result from a different runner.
- Both arms contain slow outlier trials (0.88 s against a typical 0.50 to 0.55 s), which
  look like noisy-neighbour interference. Medians absorb them; the means of the raw
  trials would not.
- The workflow's own pooled figures (base 0.519061 s, candidate 0.544754 s, speedup
  0.9528, 4.95% slower) equal the mean of the per-round medians used above. The two
  calculations agree.
- Other A-B-B-A experiments in the same campaign failed on missing CPU features and
  produced no data, so nothing is reported for them.

## Recipe

Pinned inputs of the original run:

| Input | Value |
|---|---|
| Workflow | "Flock aligned recycling A-B-B-A", run 35289110576 |
| Benchmark repo commit | `9e2ddcecc1f631a0e2bb16b33c47a9f60e9e3102` |
| `FLOCK_SOURCE_SHA` | `1b55c6ee2c9cae3c807489293199760e5e21d52b` |
| `EXPERIMENT_SHA` | `176ac0316735bc49fd06ee3507de6da9cddf695d` |
| Batch size / threads | 262,144 / 4 |
| Per round | 1 warm-up call discarded, 3 measured calls, median taken |
| Order | base, candidate, candidate, base |

`data/rounds.json` is the `EXPERIMENT_JSON_BEGIN` .. `EXPERIMENT_JSON_END` block from
the job log, unedited apart from stripping log timestamps. Rebuild this report with
`python reports/flock/build.py`. Re-running the measurement itself needs the pinned commits
above and a GitHub Actions runner; it is not reproducible from this repository alone.
