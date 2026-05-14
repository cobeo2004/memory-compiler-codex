from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from memory_compiler_codex.python_bridge import build_command, resolve_lifecycle_script, run_process


def test_resolve_lifecycle_script_names():
    root = Path("/repo/memory-compiler")

    assert resolve_lifecycle_script(root, "session-start") == root / "hooks" / "session-start.py"
    assert resolve_lifecycle_script(root, "session-end") == root / "hooks" / "session-end.py"
    assert resolve_lifecycle_script(root, "pre-compact") == root / "hooks" / "pre-compact.py"
    assert resolve_lifecycle_script(root, "capture") == root / "hooks" / "session-end.py"


def test_resolve_lifecycle_script_rejects_unknown_command():
    with pytest.raises(ValueError, match="Unsupported lifecycle command"):
        resolve_lifecycle_script(Path("/repo/memory-compiler"), "post-tool-use")


def test_build_command_uses_uv_directory_and_python_script():
    root = Path("/repo/memory-compiler")

    bridge_command = build_command(root, "session-start")

    assert bridge_command.command == [
        "uv",
        "run",
        "--directory",
        str(root),
        "python",
        str(root / "hooks" / "session-start.py"),
    ]
    assert bridge_command.script_path == root / "hooks" / "session-start.py"


def test_run_process_captures_output(monkeypatch):
    calls = {}

    def fake_run(command, **kwargs):
        calls["command"] = command
        calls["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = run_process(["uv", "run"], '{"session_id":"s1"}')

    assert result.returncode == 0
    assert calls["command"] == ["uv", "run"]
    assert calls["kwargs"] == {
        "input": '{"session_id":"s1"}',
        "capture_output": True,
        "text": True,
        "check": False,
    }

