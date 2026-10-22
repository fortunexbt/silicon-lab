"""Environment capture. Every field is None when the platform does not expose it."""

from __future__ import annotations

import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from silicon_lab import __version__


def _run(*cmd: str) -> str | None:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=True)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() or None


def _chip() -> str | None:
    if sys.platform == "darwin":
        return _run("sysctl", "-n", "machdep.cpu.brand_string")
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return None


def _memory_bytes() -> int | None:
    if sys.platform == "darwin":
        raw = _run("sysctl", "-n", "hw.memsize")
        return int(raw) if raw else None
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (ValueError, OSError, AttributeError):
        return None


def _power_source() -> str | None:
    if sys.platform != "darwin":
        return None
    raw = _run("pmset", "-g", "batt")
    match = re.search(r"Now drawing from '([^']+)'", raw or "")
    return match.group(1) if match else None


def _thermal() -> dict[str, Any]:
    """macOS: pmset thermal warning levels. Linux: hottest thermal zone in Celsius."""
    if sys.platform == "darwin":
        raw = _run("pmset", "-g", "therm")
        limit = re.search(r"CPU_Speed_Limit\s*=\s*(\d+)", raw or "")
        return {"cpu_speed_limit": int(limit.group(1)) if limit else None, "max_zone_c": None}
    temps = []
    for zone in Path("/sys/class/thermal").glob("thermal_zone*/temp"):
        try:
            temps.append(int(zone.read_text()) / 1000)
        except (OSError, ValueError):
            continue
    return {"cpu_speed_limit": None, "max_zone_c": max(temps) if temps else None}


def snapshot() -> dict[str, Any]:
    """Quick per-run conditions: load, power source, thermals."""
    try:
        load = os.getloadavg()[0]
    except OSError:
        load = None
    return {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "load_1m": load,
        "power_source": _power_source(),
        **_thermal(),
    }


def capture() -> dict[str, Any]:
    """Machine and toolchain description, taken once per experiment."""
    return {
        "silicon_lab": __version__,
        "chip": _chip(),
        "machine": platform.machine(),
        "os": f"{platform.system()} {platform.release()}",
        "os_version": platform.version(),
        "mac_ver": platform.mac_ver()[0] or None,
        "python": platform.python_version(),
        "python_impl": platform.python_implementation(),
        "cpu_count": os.cpu_count(),
        "memory_bytes": _memory_bytes(),
        **snapshot(),
    }
