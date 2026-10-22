"""Rebuild REPORT.md from data/rounds.json (the EXPERIMENT_JSON block of the CI run)."""

import json
from pathlib import Path

from silicon_lab import report, stats

HERE = Path(__file__).parent
ARM = {"base": "A", "candidate": "B"}

ENVIRONMENT = {
    "chip": "AMD EPYC 9V45 96-Core Processor (4 threads used)",
    "os": "GitHub-hosted ubuntu-24.04, image 20260907.300.1",
    "time": "2026-09-17/18 (GitHub Actions run 35289110576)",
}

RECIPE = """\
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
"""

LIMITS = """\
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
"""


def build() -> str:
    data = json.loads((HERE / "data" / "rounds.json").read_text())
    runs = []
    for position, rnd in enumerate(data["rounds"]):
        metrics = rnd["metrics"]
        runs.append(
            {
                "block": 0,
                "position": position,
                "arm": ARM[rnd["arm"]],
                "warmup_values": metrics["warmup_trial_seconds"],
                "trials": metrics["trial_seconds"],
                "value": metrics["median_seconds"],
            }
        )
    record = {
        "label": "Flock aligned recycling: base (A) vs candidate (B), A-B-B-A on one CI VM",
        "unit": "s",
        "higher_is_better": False,
        "environment": ENVIRONMENT,
        "runs": runs,
    }
    return "\n".join(
        [
            report.render(record, stats.summarize(runs)),
            "## Headline",
            "",
            "Candidate is 4.95% slower than base on this VM (0.5448 s against 0.5191 s "
            "per verified batch), from one block with no interval. Read it as a "
            "diagnostic, not a verdict.",
            "",
            LIMITS,
            RECIPE,
        ]
    )


if __name__ == "__main__":
    (HERE / "REPORT.md").write_text(build())
