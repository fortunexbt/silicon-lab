"""Rebuild REPORT.md from data/captures.jsonl and data/ledger.json."""

import json
import statistics
from pathlib import Path

from silicon_lab import stats

HERE = Path(__file__).parent
DATA = HERE / "data"

REPEATS = [
    "makeup-lean-full1920-jungle-02",
    "makeup-lean-full1920-jungle-03",
    "makeup-lean-full1920-jungle-04",
]

# (question, A id, B id). Each pair is two separate captures, not an A-B-B-A block.
PAIRS = [
    (
        "Faithful 32x texture pack vs vanilla textures, jungle, R12/S12",
        "makeup-lean-r12s12-full1920-jungle-screen-02",
        "makeup-faithful32-r12s12-full1920-jungle-01",
    ),
    (
        "ZGC vs G1 garbage collector, fresh flight",
        "makeup-lean-entity-g1-full1920-freshflight-01",
        "makeup-lean-entity-zgc-full1920-freshflight-01",
    ),
    (
        "Second flight vs first flight, same build",
        "makeup-core-entity-full1920-freshflight-01",
        "makeup-core-entity-full1920-warmflight-01",
    ),
    (
        "Second flight vs first flight, C2ME build",
        "makeup-core-entity-c2me-full1920-freshflight-01",
        "makeup-core-entity-c2me-full1920-warmflight-01",
    ),
    (
        "Frame cap 90 vs 120, vsync off, jungle (neither cap binds)",
        "makeup-r12s12-full1920-cap90-vsyncoff-jungle-02",
        "makeup-r12s12-full1920-cap120-vsyncoff-jungle-01",
    ),
    (
        "Vsync on vs off at a 60 FPS cap (cap-bound by construction)",
        "makeup-r12s12-full1920-cap60-vsyncon-jungle-01",
        "makeup-r12s12-full1920-cap60-vsyncoff-jungle-01",
    ),
]

IDS = sorted(set(REPEATS) | {i for _, a, b in PAIRS for i in (a, b)})


def captures() -> dict[str, dict]:
    lines = (DATA / "captures.jsonl").read_text().splitlines()
    return {r["id"]: r for r in map(json.loads, lines)}


def repeat_section(caps: dict[str, dict]) -> tuple[list[str], float]:
    values = [caps[i]["average_fps"] for i in REPEATS]
    ci = stats.bootstrap_ci(values)
    spread = max(values) - min(values)
    lines = [
        "## Headline: repeat noise on one configuration",
        "",
        f"Three 60 s captures of the same MakeUp lean profile on the jungle route, 1920x1200 "
        f"output, averaged **{statistics.fmean(values):.2f} CPU FPS** "
        f"(sample SD {statistics.stdev(values):.2f}, range {min(values):.2f} to "
        f"{max(values):.2f}). The seeded 95% bootstrap interval of the mean over n=3 is "
        f"[{ci[0]:.2f}, {ci[1]:.2f}]; with three values it is only a rough guide. "
        f"This is the only run-to-run noise estimate in the evidence, so the pair table "
        f"below treats differences within {spread:.1f} FPS as inside the noise.",
        "",
        "| Capture | Average CPU FPS | p95 interval (ms) | p99 interval (ms) | Intervals over 33 ms |",
        "|---|---:|---:|---:|---:|",
    ]
    for i in REPEATS:
        c = caps[i]
        lines.append(
            f"| {i} | {c['average_fps']:.2f} | {c['p95_ms']:.2f} | {c['p99_ms']:.2f} | "
            f"{c['interval_counts_gt_ms']['33']} |"
        )
    lines.append("")
    return lines, spread


def verdict(diff: float, spread: float) -> str:
    return "inside noise" if abs(diff) <= spread else "outside noise"


def pair_section(caps: dict[str, dict], spread: float) -> list[str]:
    lines = [
        "## Matched pairs",
        "",
        "Each row compares two separate captures: B minus A in CPU FPS. There is one capture per "
        "arm, so there is no interval and no drift control; the last column compares the "
        f"difference to the {spread:.1f} FPS repeat range above.",
        "",
        "| Question | A | B | A FPS | B FPS | B - A | Change | Against noise |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for question, a, b in PAIRS:
        fa, fb = caps[a]["average_fps"], caps[b]["average_fps"]
        lines.append(
            f"| {question} | `{a}` | `{b}` | {fa:.2f} | {fb:.2f} | {fb - fa:+.2f} | "
            f"{(fb - fa) / fa * 100:+.1f}% | {verdict(fb - fa, spread)} |"
        )
    lines += [
        "",
        "The flight rows are an order effect, not a build effect: both pairs show the second "
        "flight over the same route about 5.5 FPS faster than the first, in two different "
        "builds, so first-flight captures are biased low and the later flight is the fairer "
        "number. The 60 FPS vsync rows land on the cap, so they say nothing about rendering "
        "cost. The cap 90 and 120 rows sit at about 80 FPS, below both caps, so they show the "
        "cap setting alone did not change throughput.",
        "",
    ]
    return lines


def ledger_section(ledger: dict, caps: dict[str, dict]) -> list[str]:
    families = {f["id"]: f for f in ledger["experiment_families"]}
    texture = families["faithful-texture-pack"]["comparison"]
    lines = [
        "## River screen, quoted from the ledger",
        "",
        "The ledger also records a river screen for the texture-pack comparison. Its raw capture "
        f"is not in the evidence index, so these two numbers are quoted: vanilla "
        f"{texture['vanilla_texture_river_fps']} against Faithful 32x "
        f"{texture['faithful_32x_river_fps']} CPU FPS "
        f"({texture['faithful_32x_river_fps'] - texture['vanilla_texture_river_fps']:+.2f}). "
        f'The ledger\'s own reading: "{texture["uncertainty"]}"',
        "",
    ]
    return lines


def limits_section(ledger: dict, caps: dict[str, dict]) -> list[str]:
    campaign = ledger["campaign"]
    measurement = ledger["measurement"]
    unreviewed = sum(1 for i in IDS if caps[i]["status"] == "unreviewed")
    return [
        "## Limits",
        "",
        f"- Scope: {campaign['claim_boundary']} The campaign ran {campaign['date_scope']} on a "
        f"{campaign['machine']['model']} ({campaign['machine']['cpu_cores']} CPU cores, "
        f"{campaign['machine']['gpu_cores']} GPU cores, {campaign['machine']['memory_gib']} GiB).",
        f"- Metric: {measurement['metric']} It is not "
        + ", ".join(m.lower() for m in measurement["not_measured"])
        + ".",
        f"- {unreviewed} of the {len(IDS)} captures used here are marked `unreviewed` in the "
        "evidence index: the FPS is kept as source evidence, but integrity and visual validity "
        "were not reviewed. Those marks come from the source project and are carried over "
        "unchanged.",
        "- Three repeats give a rough noise band, not a reliable interval. A band measured on "
        "the jungle route may not describe other routes.",
        "- The pairs are not A-B-B-A: one capture per arm, taken at different times, so drift "
        "and the order effect shown above are confounded with the compared setting.",
        "- Shader quality was not held equal across profiles, so FPS here is not a ranking of "
        "shader packs.",
        "",
    ]


RECIPE = """\
## Recipe and sources

| Input | Value |
|---|---|
| Source project | `minecraft-apple-silicon-framework`, commit `d9b3204a9959cdb25e3c6da2bed66affd9bd3885`, MIT licence |
| Source files | `evidence/captures.jsonl`, `evidence/ledger.json` |
| Selection | the capture ids listed in `PAIRS` and `REPEATS` in `build.py` |
| Extract | `cd reports/shader && python extract.py <path to evidence>` |
| Rebuild | `python reports/shader/build.py` |

`data/captures.jsonl` holds the selected records unedited, one per line, and `data/ledger.json`
is a byte copy. Each record carries the `source_ref` and `source_sha256` of the original
summary file, which is not copied here. This repository ran no Minecraft or shader
benchmark; it recomputes differences and the interval from the committed records.
"""


def build() -> str:
    caps = captures()
    ledger = json.loads((DATA / "ledger.json").read_text())
    header = [
        "# Shader frame production on a base M4: repeat noise and matched pairs",
        "",
    ]
    repeat, spread = repeat_section(caps)
    return "\n".join(
        header
        + repeat
        + pair_section(caps, spread)
        + ledger_section(ledger, caps)
        + limits_section(ledger, caps)
        + [RECIPE]
    )


if __name__ == "__main__":
    (HERE / "REPORT.md").write_text(build())
