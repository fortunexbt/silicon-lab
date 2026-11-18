# silicon-lab

silicon-lab tells you whether configuration B beats configuration A on one machine, and by how much. It runs both arms in A-B-B-A blocks, keeps the raw timings in JSON and reports the mean paired difference with a bootstrap interval.

## Quick start

```
pip install -e .
silicon-lab run --blocks 6 --out result.json --hash-rounds 20000 40000
silicon-lab report result.json
```

The built-in workload is a SHA-256 chain, so this runs anywhere with Python 3.10 or later. To time your own programs, swap `--hash-rounds` for `--cmd-a "..." --cmd-b "..."`. Each call runs the command once as a subprocess and times it wall-clock.

## Method

In an A, B, B, A block a linear drift such as a thermal ramp adds the same amount to both arms and cancels in the difference. Each run discards `--warmup` calls (default 1, still recorded) and takes the median of `--trials` calls (default 3). The interval is a 95% percentile bootstrap of the mean B minus A over blocks, with 10,000 resamples and seed 20261023, so it needs at least two blocks (`--blocks` defaults to 4). Each record also stores the chip, OS, memory, load, power source and thermal state.

## Reports

Three earlier measurements, rebuilt from their committed raw data. CI reruns each `build.py` and fails if its `REPORT.md` changes. None was remeasured here.

- [flock](reports/flock/REPORT.md) found a BLAKE3 candidate 4.95% slower than base in one A-B-B-A block on a GitHub Actions VM. One block gives no interval.
- [qwen38](reports/qwen38/REPORT.md) measured a median 42.13 tok/s decode for a local 35B model on a 24 GB M4. It isn't a paired design.
- [shader](reports/shader/REPORT.md) sets a 1.3 FPS noise band from three repeat captures of one Minecraft shader profile, then reads six matched pairs against it.

Run the checks with `pip install -e ".[dev]"` then `ruff check . && ruff format --check . && pytest`.

## Sources and licence

The shader data comes from [minecraft-apple-silicon-framework](https://github.com/fortunexbt/minecraft-apple-silicon-framework) (MIT) and the flock data from one run of [flock-baseline-runner](https://github.com/fortunexbt/flock-baseline-runner). The qwen38 figures come from a local llama.cpp tuning project. Only throughput numbers are published, because the model's licence wasn't verified.

silicon-lab is MIT licensed.
