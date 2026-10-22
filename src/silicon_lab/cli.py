"""Command line: `silicon-lab run` and `silicon-lab report`."""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path

from silicon_lab import report, runner


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="silicon-lab", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run an A-B-B-A experiment and write raw JSON")
    run.add_argument("--out", type=Path, required=True, help="raw JSON output path")
    run.add_argument("--label", default="")
    run.add_argument("--blocks", type=int, default=4)
    run.add_argument("--trials", type=int, default=3, help="measured calls per run")
    run.add_argument("--warmup", type=int, default=1, help="discarded calls per run")
    run.add_argument(
        "--hash-rounds",
        type=int,
        nargs=2,
        metavar=("A", "B"),
        help="built-in CPU workload: SHA-256 chain length for arm A and arm B",
    )
    run.add_argument("--cmd-a", help="shell-quoted command timed as arm A")
    run.add_argument("--cmd-b", help="shell-quoted command timed as arm B")

    rep = sub.add_parser("report", help="render a Markdown report from raw JSON")
    rep.add_argument("raw", type=Path)
    rep.add_argument("--out", type=Path, help="write here instead of stdout")
    return parser


def _workloads(args: argparse.Namespace) -> dict[str, runner.Workload]:
    if args.hash_rounds:
        a, b = args.hash_rounds
        return {"A": runner.hash_workload(a), "B": runner.hash_workload(b)}
    if args.cmd_a and args.cmd_b:
        return {
            "A": runner.command_workload(shlex.split(args.cmd_a)),
            "B": runner.command_workload(shlex.split(args.cmd_b)),
        }
    raise SystemExit("run needs --hash-rounds A B or both --cmd-a and --cmd-b")


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "run":
        config = (
            {"hash_rounds": args.hash_rounds}
            if args.hash_rounds
            else {"cmd_a": args.cmd_a, "cmd_b": args.cmd_b}
        )
        record = runner.run_experiment(
            _workloads(args),
            blocks=args.blocks,
            trials=args.trials,
            warmup=args.warmup,
            label=args.label,
            config=config,
        )
        args.out.write_text(json.dumps(record, indent=2) + "\n")
        print(f"wrote {args.out}", file=sys.stderr)
        return 0
    text = report.render(json.loads(args.raw.read_text()))
    if args.out:
        args.out.write_text(text)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
