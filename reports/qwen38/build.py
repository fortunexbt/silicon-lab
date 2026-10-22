"""Rebuild REPORT.md from data/pareto.jsonl and data/queue_excerpt.log."""

import json
import statistics
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"
WARM_REPEAT_TAGS = ("q3", "q3r2", "q3r2idle", "q3master")


def headline_rows() -> list[dict]:
    rows = []
    for line in (DATA / "queue_excerpt.log").read_text().splitlines():
        if line.startswith("{"):
            rows.append(json.loads(line))
    return rows


def summary_line() -> dict:
    for line in (DATA / "queue_excerpt.log").read_text().splitlines():
        if line.startswith("SUMMARY "):
            return json.loads(line[len("SUMMARY ") :])
    raise ValueError("no SUMMARY line")


def tasks_line() -> dict:
    for line in (DATA / "queue_excerpt.log").read_text().splitlines():
        if line.startswith("TASKS "):
            return json.loads(line[len("TASKS ") :])
    raise ValueError("no TASKS line")


def pareto() -> list[dict]:
    return [json.loads(line) for line in (DATA / "pareto.jsonl").read_text().splitlines()]


def headline_section() -> list[str]:
    rows = headline_rows()
    summary = summary_line()
    tasks = tasks_line()
    values = [r["decode_tps"] for r in rows]
    assert statistics.median(values) == summary["median_decode_tps"]
    lines = [
        "# Local decode speed of Cyber-Tiel-Coder-35B-A3B on a 24 GB M4",
        "",
        "## Headline",
        "",
        f"**{summary['median_decode_tps']} tok/s** median decode (greedy, MTP depth 2 plus n-gram "
        f"drafting) over five prompts, one clean run on 2026-10-19 on an Apple M4 MacBook "
        f"(24 GB, AC power, load 2.23). Per-prompt range {min(values)} to {max(values)} tok/s; "
        f"mean {summary['mean_decode_tps']}; median time to first token "
        f"{summary['median_ttft_s']} s.",
        "",
        "This is not an A-B-B-A experiment and has no confidence interval. The spread above is "
        "across prompts, which differ in how predictable their text is, not across repeated "
        "paired blocks. The repeat analysis below is the only estimate of run-to-run noise.",
        "",
        "| Prompt | Decode (tok/s) | TTFT (s) | Tokens |",
        "|---|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(f"| {r['prompt']} | {r['decode_tps']} | {r['ttft_s']} | {r['n']} |")
    lines += [
        "",
        f"Task evals on the same server: tool-call accuracy {tasks['tool_call_acc']}, "
        f"HumanEval 40-problem pass@1 {tasks['humaneval40_pass1']} "
        f"(elapsed {tasks['elapsed_s']} s). Forty problems is a small sample: one problem is "
        "2.5 points.",
        "",
    ]
    return lines


def repeat_section(rows: list[dict]) -> list[str]:
    repeats = [r for r in rows if r["config"] == "d2_ub512" and r["tag"] in WARM_REPEAT_TAGS]
    values = [r["decode_short_tps"] for r in repeats]
    warm = values[1:]
    lines = [
        "## Run-to-run noise",
        "",
        "The same configuration (`d2_ub512`, depth 2 with -ub 512) was measured several times "
        "across the sweep, which gives a rough noise estimate. The first run is cold.",
        "",
        "| Tag | Short decode (tok/s) |",
        "|---|---:|",
    ]
    lines += [f"| {r['tag']} | {r['decode_short_tps']} |" for r in repeats]
    lines += [
        "",
        f"Cold first run {values[0]}; the {len(warm)} later runs span {min(warm)} to {max(warm)} "
        f"tok/s (mean {statistics.mean(warm):.2f}, sample SD {statistics.stdev(warm):.2f}). "
        f"Treat differences under about {max(warm) - min(warm):.1f} tok/s between configurations "
        "as noise. The last row used a newer llama.cpp build, so it also mixes in a build "
        "difference.",
        "",
    ]
    return lines


def pareto_section(rows: list[dict]) -> list[str]:
    lines = [
        "## Full sweep",
        "",
        f"All {len(rows)} rows of `pareto.jsonl`, one measurement each, sorted by short decode. "
        "Every row is flagged clean (AC power, load at most 6.0). Prefill and long-decode "
        "figures are tok/s; accept is the draft acceptance rate.",
        "",
        "| Tag | Config | Short decode | 32k decode | Prefill 10k | Prefill 32k | Accept | Load |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in sorted(rows, key=lambda r: -r["decode_short_tps"]):
        lines.append(
            f"| {r['tag']} | {r['config']} | {r['decode_short_tps']} | {r['decode_32k_tps']} | "
            f"{r['prefill_10k_tps']} | {r['prefill_32k_tps']} | {r['accept']} | {r['load']} |"
        )
    lines += [
        "",
        "Several `dflash` rows decode faster on the short prompt (about 45.6 tok/s) than the "
        "depth-2 default, with 32k decode no better. Those are single measurements within a "
        "few tok/s of the noise band above, and this report does not claim they are "
        "faster or slower.",
        "",
    ]
    return lines


LIMITS = """\
## Limits

- One machine, one clean headline run. No paired blocks, no interval. The spread is across
  prompts.
- The sweep rows are single measurements, with the A-B-B-A drift control absent. Row order in
  the file is the order they ran, and configs were not interleaved, so thermal or memory
  drift is confounded with config.
- The headline run used the Homebrew `llama-server` 0.7.0 binary; its exact build number was
  not recorded. Only the `q3master` row is tied to a recorded build (master build 11738,
  commit `f174553e1621c6a22a64e7bfcbb58d3a5c49e6fb`).
- The model licence for Cyber-Tiel-Coder-35B-A3B was not verified, so no weights or outputs
  are republished here, only throughput numbers.
- Decode speed under speculative drafting depends on how repetitive the text is. The
  `prose` prompt (24.18 tok/s) and `codecont` (46.21 tok/s) differ by nearly 2x on the same
  model and settings. Do not quote one number as general speed.
- Memory was tight: swap was 4.3 GB at the start of the headline run and the sweep rows
  record swap and pageout deltas. A fresh reboot resets `iogpu.wired_limit_mb`.
"""

RECIPE = """\
## Recipe

| Input | Value |
|---|---|
| Machine | Apple M4, 24 GB unified memory, AC power |
| Server | `data/serve_cyber_omp.sh` (copy of the original script), depth 2 |
| Model file | `Cyber-Tiel-Coder-35B-A3B-MTP-UD-Q3_K_XL.gguf`, served as `cyber-tiel-35b` |
| Server flags | `-ngl 99 -fa on -c 65536 -np 1 -ub 2048 --temp 0 --jinja` |
| Speculation | `--spec-type ngram-mod,draft-mtp --spec-draft-n-max 2`, ngram-mod n-match 24, n-min 48, n-max 64 |
| Wired limit | `sudo sysctl iogpu.wired_limit_mb=20480` (resets on reboot) |
| Benchmark | `bench_server.py --url http://127.0.0.1:8080/v1 --model cyber-tiel-35b --temp 0 --tag cyber_tiel_depth2` |
| Task evals | `eval_tasks.py` with the same url, model and tag |

`bench_server.py`, `eval_tasks.py` and `pareto_sweep.py` live in the source project and
are not part of this repository. `data/pareto.jsonl` is the unedited
sweep log and `data/queue_excerpt.log` is lines 47 to 58 of its `queue.log`. Rebuild this
report with `python reports/qwen38/build.py`. Reproducing the measurement needs the model
file, the scripts and an M4-class machine. This repository ran no model.
"""


def build() -> str:
    rows = pareto()
    return "\n".join(
        headline_section() + repeat_section(rows) + pareto_section(rows) + [LIMITS, RECIPE]
    )


if __name__ == "__main__":
    (HERE / "REPORT.md").write_text(build())
