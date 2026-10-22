import json

import pytest

from silicon_lab import cli, report, runner, stats
from silicon_lab.schedule import abba


def make_runs(a_values, b_values):
    """One A and one B run per block, values given per block."""
    runs = []
    for block, (a, b) in enumerate(zip(a_values, b_values, strict=True)):
        runs.append({"block": block, "arm": "A", "value": a})
        runs.append({"block": block, "arm": "B", "value": b})
    return runs


def test_abba_order_and_length():
    slots = list(abba(3))
    assert len(slots) == 12
    assert [s.arm for s in slots[:8]] == list("ABBAABBA")
    assert [s.block for s in slots] == [0] * 4 + [1] * 4 + [2] * 4
    assert [s.position for s in slots[:4]] == [0, 1, 2, 3]


def test_abba_rejects_zero_blocks():
    with pytest.raises(ValueError):
        list(abba(0))


def test_abba_cancels_linear_drift():
    drift = lambda position: 0.5 * position  # noqa: E731
    runs = []
    for slot in abba(2):
        base = 10.0 if slot.arm == "A" else 12.0
        runs.append({"block": slot.block, "arm": slot.arm, "value": base + drift(slot.position)})
    assert stats.paired_diffs(runs) == [pytest.approx(2.0)] * 2


def test_paired_diffs_skip_warmup_and_incomplete_blocks():
    runs = make_runs([1.0, 2.0], [3.0, 5.0])
    runs.append({"block": 0, "arm": "A", "value": 999.0, "warmup": True})
    runs.append({"block": 2, "arm": "A", "value": 7.0})
    assert stats.paired_diffs(runs) == [2.0, 3.0]


def test_bootstrap_is_seeded_and_brackets_the_mean():
    diffs = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    first = stats.bootstrap_ci(diffs, resamples=2000, seed=1)
    assert first == stats.bootstrap_ci(diffs, resamples=2000, seed=1)
    lo, hi = first
    assert lo < 3.5 < hi
    assert lo >= 1.0 and hi <= 6.0


def test_bootstrap_constant_values_collapse():
    assert stats.bootstrap_ci([2.0, 2.0, 2.0], resamples=500) == (2.0, 2.0)


def test_bootstrap_needs_two_values():
    assert stats.bootstrap_ci([1.0]) is None


def test_summarize_single_block_has_no_ci():
    summary = stats.summarize(make_runs([10.0], [11.0]))
    assert summary["ci"] is None
    assert summary["mean_diff"] == pytest.approx(1.0)
    assert summary["relative_change"] == pytest.approx(0.1)


def test_summarize_requires_a_complete_block():
    with pytest.raises(ValueError):
        stats.summarize([{"block": 0, "arm": "A", "value": 1.0}])


def test_run_experiment_records_everything_and_takes_median():
    calls = {"A": iter([9.0, 3.0, 1.0, 2.0] * 8), "B": iter([9.0, 6.0, 4.0, 5.0] * 8)}
    workloads = {arm: (lambda arm=arm: next(calls[arm])) for arm in "AB"}
    record = runner.run_experiment(workloads, blocks=2, trials=3, warmup=1, label="fake")
    assert len(record["runs"]) == 8
    first = record["runs"][0]
    assert first["warmup_values"] == [9.0]
    assert first["trials"] == [3.0, 1.0, 2.0]
    assert first["value"] == 2.0
    assert record["environment"]["python"]
    assert "load_1m" in first["conditions"]
    assert stats.summarize(record["runs"])["mean_diff"] == pytest.approx(3.0)


def test_hash_workload_is_deterministic_in_work_not_time():
    assert runner.hash_workload(10)() >= 0
    assert runner.hash_workload(0)() >= 0


def test_report_contents():
    record = {
        "label": "demo",
        "unit": "s",
        "higher_is_better": False,
        "environment": {"chip": "test-chip"},
        "runs": make_runs([1.0, 1.1, 0.9], [2.0, 2.2, 1.8]),
    }
    text = report.render(record)
    assert text.startswith("# demo")
    assert "bootstrap CI" in text
    assert "B is worse than A" in text
    assert "test-chip" in text


def test_report_flags_missing_interval():
    record = {
        "label": "",
        "unit": "tok/s",
        "higher_is_better": True,
        "environment": {},
        "runs": make_runs([1.0], [2.0]),
    }
    assert "n/a" in report.render(record)


def test_cli_run_then_report(tmp_path, capsys):
    raw = tmp_path / "raw.json"
    code = cli.main(
        ["run", "--out", str(raw), "--blocks", "2", "--trials", "2", "--hash-rounds", "50", "500"]
    )
    assert code == 0
    record = json.loads(raw.read_text())
    assert record["config"]["hash_rounds"] == [50, 500]
    assert [r["arm"] for r in record["runs"][:4]] == list("ABBA")
    md = tmp_path / "report.md"
    assert cli.main(["report", str(raw), "--out", str(md)]) == 0
    assert "## Result" in md.read_text()
    # 10x more hashing in B must be slower, whatever the machine
    assert stats.summarize(record["runs"])["mean_diff"] > 0


def test_cli_run_requires_workload(tmp_path):
    with pytest.raises(SystemExit):
        cli.main(["run", "--out", str(tmp_path / "x.json")])
