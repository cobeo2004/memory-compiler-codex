from __future__ import annotations

import io
import os
import subprocess
import sys
from pathlib import Path

from memory_compiler_codex.cli import main


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "memory-compiler"


class _FakeStdin(io.StringIO):
    def isatty(self) -> bool:
        return False


def _subprocess_env(out_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["FAKE_MEMORY_COMPILER_OUT"] = str(out_path)
    pythonpath = env.get("PYTHONPATH")
    src_path = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = src_path if not pythonpath else os.pathsep.join([src_path, pythonpath])
    return env


def test_python_module_cli_writes_raw_payload(tmp_path):
    out_path = tmp_path / "memory-compiler.out"
    payload = '{"session_id":"s1","hook_event_name":"SessionStart"}'

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "memory_compiler_codex",
            "session-start",
            "--memory-compiler-root",
            str(FIXTURE_ROOT),
        ],
        cwd=REPO_ROOT,
        env=_subprocess_env(out_path),
        input=payload,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert out_path.read_text(encoding="utf-8").strip() == payload


def test_main_writes_normalised_event_when_stdin_is_not_json(tmp_path, monkeypatch):
    out_path = tmp_path / "memory-compiler.out"
    monkeypatch.setenv("FAKE_MEMORY_COMPILER_OUT", str(out_path))
    monkeypatch.setattr(sys, "stdin", _FakeStdin("not-json"))

    exit_code = main(["pre-compact", "--memory-compiler-root", str(FIXTURE_ROOT)])

    assert exit_code == 0
    output = out_path.read_text(encoding="utf-8")
    assert '"command":"pre-compact"' in output
    assert '"parse_error"' in output
