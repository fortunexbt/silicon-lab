"""Markdown report from a raw experiment record."""

from __future__ import annotations

from typing import Any

from silicon_lab import stats


def _fmt(value: float | None, unit: str = "") -> str:
    if value is None:
        return "n/a"
    return f"{value:.4g}{' ' + unit if unit else ''}"


def _signed(value: float) -> str:
    return f"{value:+.4g}"


def verdict(summary: dict[str, Any], higher_is_better: bool) -> str:
    ci = summary["ci"]
    if ci is None:
        return "Not enough blocks for an interval; treat the difference as a single observation."
    lo, hi = ci
    if lo <= 0 <= hi:
        return "The interval contains zero: no detectable difference at this sample size."
    b_better = (summary["mean_diff"] > 0) == higher_is_better
    return f"The interval excludes zero: B is {'better' if b_better else 'worse'} than A."


def render(record: dict[str, Any], summary: dict[str, Any] | None = None) -> str:
    """Render the report. `summary` is recomputed from the runs when omitted."""
    summary = summary or stats.summarize(record["runs"])
    unit = record["unit"]
    pct = summary["relative_change"]
    ci = summary["ci"]
    level = int(summary["ci_level"] * 100)
    environment = record["environment"]
    lines = [
        f"# {record['label'] or 'A/B experiment'}",
        "",
        "## Result",
        "",
        f"- A mean: {_fmt(summary['mean_a'], unit)}",
        f"- B mean: {_fmt(summary['mean_b'], unit)}",
        f"- Paired difference (B - A): **{_signed(summary['mean_diff'])} {unit}**"
        + (f" ({pct * 100:+.2f}%)" if pct is not None else ""),
        f"- {level}% bootstrap CI: "
        + (f"[{_signed(ci[0])}, {_signed(ci[1])}] {unit}" if ci else "n/a"),
        f"- Blocks: {summary['blocks']} (A-B-B-A each); "
        f"{summary['resamples']} resamples, seed {summary['seed']}",
        f"- {verdict(summary, record['higher_is_better'])}",
        "",
        "## Blocks",
        "",
        f"| Block | A mean ({unit}) | B mean ({unit}) | B - A ({unit}) |",
        "|---:|---:|---:|---:|",
    ]
    for block, arms in stats.block_means(record["runs"]).items():
        if "A" in arms and "B" in arms:
            diff = _signed(arms["B"] - arms["A"])
            lines.append(f"| {block} | {_fmt(arms['A'])} | {_fmt(arms['B'])} | {diff} |")
    lines += [
        "",
        "## Runs",
        "",
        f"| Block | Pos | Arm | Warm-up discarded ({unit}) | Trials ({unit}) "
        f"| Run value ({unit}) |",
        "|---:|---:|:--:|---|---|---:|",
    ]
    for run in record["runs"]:
        warm = ", ".join(_fmt(v) for v in run.get("warmup_values", [])) or "-"
        trials = ", ".join(_fmt(v) for v in run.get("trials", []))
        lines.append(
            f"| {run['block']} | {run.get('position', '-')} | {run['arm']} | {warm} | {trials} | "
            f"{_fmt(run['value'])} |"
        )
    lines += ["", "## Environment", ""]
    for key in ("chip", "os", "python", "cpu_count", "memory_bytes", "power_source", "time"):
        if environment.get(key) is not None:
            lines.append(f"- {key}: {environment[key]}")
    lines += [
        "",
        "## Method",
        "",
        "Runs follow A-B-B-A within each block, so linear drift cancels in the block "
        "difference. Warm-up calls are discarded but kept in the raw record. A run's value is "
        "the median of its trials. The interval is a seeded percentile bootstrap of the mean "
        "over block differences; with fewer than two blocks it is not defined.",
        "",
    ]
    return "\n".join(lines)
