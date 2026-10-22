"""Paired-difference statistics with a seeded percentile bootstrap."""

from __future__ import annotations

import random
import statistics
from collections.abc import Sequence
from typing import Any

DEFAULT_RESAMPLES = 10_000
DEFAULT_SEED = 20261023


def block_means(runs: Sequence[dict[str, Any]]) -> dict[int, dict[str, float]]:
    """Mean run value per arm in each block, warm-up runs excluded."""
    grouped: dict[int, dict[str, list[float]]] = {}
    for run in runs:
        if run.get("warmup"):
            continue
        grouped.setdefault(run["block"], {}).setdefault(run["arm"], []).append(run["value"])
    return {
        block: {arm: statistics.fmean(vals) for arm, vals in arms.items()}
        for block, arms in sorted(grouped.items())
    }


def paired_diffs(runs: Sequence[dict[str, Any]]) -> list[float]:
    """Per-block B minus A. Blocks missing either arm are skipped."""
    return [
        arms["B"] - arms["A"] for arms in block_means(runs).values() if "A" in arms and "B" in arms
    ]


def bootstrap_ci(
    values: Sequence[float],
    level: float = 0.95,
    resamples: int = DEFAULT_RESAMPLES,
    seed: int = DEFAULT_SEED,
) -> tuple[float, float] | None:
    """Percentile bootstrap CI of the mean. None when fewer than two values."""
    if len(values) < 2:
        return None
    rng = random.Random(seed)
    n = len(values)
    means = sorted(statistics.fmean(rng.choices(values, k=n)) for _ in range(resamples))
    tail = (1 - level) / 2
    lo = means[int(tail * resamples)]
    hi = means[min(resamples - 1, int((1 - tail) * resamples))]
    return lo, hi


def summarize(
    runs: Sequence[dict[str, Any]],
    level: float = 0.95,
    resamples: int = DEFAULT_RESAMPLES,
    seed: int = DEFAULT_SEED,
) -> dict[str, Any]:
    """Headline numbers: mean A and B, mean paired difference, relative change, CI."""
    paired = [m for m in block_means(runs).values() if "A" in m and "B" in m]
    if not paired:
        raise ValueError("no block has both an A and a B run")
    diffs = [m["B"] - m["A"] for m in paired]
    mean_a = statistics.fmean(m["A"] for m in paired)
    mean_b = statistics.fmean(m["B"] for m in paired)
    mean_diff = statistics.fmean(diffs)
    ci = bootstrap_ci(diffs, level, resamples, seed)
    return {
        "blocks": len(diffs),
        "mean_a": mean_a,
        "mean_b": mean_b,
        "diffs": diffs,
        "mean_diff": mean_diff,
        "relative_change": mean_diff / mean_a if mean_a else None,
        "ci_level": level,
        "ci": list(ci) if ci else None,
        "resamples": resamples,
        "seed": seed,
    }
