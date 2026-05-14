from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


SCRIPT_NAMES = {
    "session-start": "session-start.py",
    "session-end": "session-end.py",
    "pre-compact": "pre-compact.py",
    "capture": "session-end.py",
}


@dataclass(frozen=True)
class BridgeCommand:
    command: list[str]
    script_path: Path


def resolve_lifecycle_script(memory_compiler_root: Path, lifecycle: str) -> Path:
    try:
        script_name = SCRIPT_NAMES[lifecycle]
    except KeyError as exc:
        raise ValueError(f"Unsupported lifecycle command: {lifecycle}") from exc
    return memory_compiler_root / "hooks" / script_name


def build_command(memory_compiler_root: Path, lifecycle: str) -> BridgeCommand:
    script_path = resolve_lifecycle_script(memory_compiler_root, lifecycle)
    return BridgeCommand(
        command=[
            "uv",
            "run",
            "--directory",
            str(memory_compiler_root),
            "python",
            str(script_path),
        ],
        script_path=script_path,
    )


def run_process(command: Sequence[str], stdin: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )

