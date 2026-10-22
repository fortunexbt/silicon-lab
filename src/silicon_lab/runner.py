"""Run an A/B experiment on the A-B-B-A schedule and return the raw record."""

from __future__ import annotations

import hashlib
import statistics
import subprocess
import time
from collections.abc import Callable, Mapping
from typing import Any

from silicon_lab import env
from silicon_lab.schedule import abba

SCHEMA = 1

Workload = Callable[[], float]
"""One measurement. Returns the metric value, here always seconds."""


def hash_workload(rounds: int) -> Workload:
    """Deterministic CPU workload: a chain of `rounds` SHA-256 digests."""

    def run() -> float:
        digest = b"silicon-lab"
        start = time.perf_counter()
        for _ in range(rounds):
            digest = hashlib.sha256(digest).digest()
        return time.perf_counter() - start

    return run


def command_workload(argv: list[str]) -> Workload:
    """Wall-clock seconds of one subprocess run. A non-zero exit raises."""

    def run() -> float:
        start = time.perf_counter()
        subprocess.run(argv, check=True, capture_output=True)
        return time.perf_counter() - start

    return run


def run_experiment(
    workloads: Mapping[str, Workload],
    blocks: int,
    trials: int = 3,
    warmup: int = 1,
    label: str = "",
    config: dict[str, Any] | None = None,
    unit: str = "s",
    higher_is_better: bool = False,
) -> dict[str, Any]:
    """Execute `blocks` A-B-B-A blocks.

    Each run discards `warmup` calls, keeps their raw values for the record, then
    takes `trials` calls and uses the median as the run value.
    """
    if trials < 1 or warmup < 0:
        raise ValueError("trials must be >= 1 and warmup >= 0")
    runs = []
    for slot in abba(blocks):
        work = workloads[slot.arm]
        conditions = env.snapshot()
        warm = [work() for _ in range(warmup)]
        measured = [work() for _ in range(trials)]
        runs.append(
            {
                "block": slot.block,
                "position": slot.position,
                "arm": slot.arm,
                "warmup": False,
                "warmup_values": warm,
                "trials": measured,
                "value": statistics.median(measured),
                "conditions": conditions,
            }
        )
    return {
        "schema": SCHEMA,
        "label": label,
        "unit": unit,
        "higher_is_better": higher_is_better,
        "environment": env.capture(),
        "config": {"blocks": blocks, "trials": trials, "warmup": warmup, **(config or {})},
        "runs": runs,
    }
