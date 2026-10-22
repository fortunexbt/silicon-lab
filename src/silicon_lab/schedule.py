"""A-B-B-A run ordering.

Within one block the order is A, B, B, A. Any linear drift (thermal ramp,
cache warm-up, background load) adds the same amount to both arms, so it
cancels in the per-block difference.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import NamedTuple

PATTERN = ("A", "B", "B", "A")


class Slot(NamedTuple):
    block: int
    position: int
    arm: str


def abba(blocks: int) -> Iterator[Slot]:
    """Yield `blocks` consecutive A-B-B-A blocks as (block, position, arm)."""
    if blocks < 1:
        raise ValueError("blocks must be at least 1")
    for block in range(blocks):
        for position, arm in enumerate(PATTERN):
            yield Slot(block, position, arm)
