"""Copy the captures this report uses out of the shader project's evidence directory.

Usage: python extract.py <path to minecraft-apple-silicon-framework/evidence>

The selection lives in build.py (IDS). The ledger is copied whole. Output goes to data/.
"""

import json
import shutil
import sys
from pathlib import Path

from build import IDS

HERE = Path(__file__).parent


def main(evidence: Path) -> None:
    wanted = set(IDS)
    rows = [json.loads(line) for line in (evidence / "captures.jsonl").read_text().splitlines()]
    chosen = [r for r in rows if r["id"] in wanted]
    missing = wanted - {r["id"] for r in chosen}
    if missing:
        raise SystemExit(f"missing from captures.jsonl: {sorted(missing)}")
    data = HERE / "data"
    data.mkdir(exist_ok=True)
    (data / "captures.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in chosen)
    )
    shutil.copyfile(evidence / "ledger.json", data / "ledger.json")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
