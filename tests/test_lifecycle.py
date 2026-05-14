from __future__ import annotations

import subprocess

from memory_compiler_codex.codex_hook_input import NormalizedCodexEvent
from memory_compiler_codex.config import AdapterConfig
from memory_compiler_codex.lifecycle import run_lifecycle


def _event(command: str, raw_payload: str = '{"session_id":"s1"}') -> NormalizedCodexEvent:
    return NormalizedCodexEvent(
        command=command,
        payload={"session_id": "s1"},
        raw_payload=raw_payload,
    )


def test_post_tool_use_skips_without_memory_compiler_root(tmp_path):
    config = AdapterConfig(memory_compiler_root=tmp_path / "missing")

    result = run_lifecycle(config, _event("post-tool-use"))

    assert result.ok is True
    assert result.exit_code == 0
    assert result.message == "post-tool-use skipped"


def test_missing_root_soft_fails_by_default(tmp_path):
    config = AdapterConfig(memory_compiler_root=tmp_path / "missing")

    result = run_lifecycle(config, _event("session-start"))

    assert result.ok is True
    assert result.exit_code == 0
    assert "root missing" in result.message


def test_missing_root_strict_exits_one(tmp_path):
    config = AdapterConfig(memory_compiler_root=tmp_path / "missing", strict=True)

    result = run_lifecycle(config, _event("session-start"))

    assert result.ok is False
    assert result.exit_code == 1


def test_missing_script_soft_fails(tmp_path):
    root = tmp_path / "memory-compiler"
    root.mkdir()
    config = AdapterConfig(memory_compiler_root=root)

    result = run_lifecycle(config, _event("session-start"))

    assert result.ok is True
    assert result.exit_code == 0
    assert "hook script missing" in result.message


def test_delegates_raw_payload_to_lifecycle_script(tmp_path, monkeypatch):
    root = tmp_path / "memory-compiler"
    hooks = root / "hooks"
    hooks.mkdir(parents=True)
    (hooks / "session-start.py").write_text("print('ok')", encoding="utf-8")
    calls = {}

    def fake_run_process(command, stdin):
        calls["command"] = command
        calls["stdin"] = stdin
        return subprocess.CompletedProcess(command, 0, stdout="hook output\n", stderr="")

    monkeypatch.setattr("memory_compiler_codex.lifecycle.run_process", fake_run_process)

    result = run_lifecycle(AdapterConfig(memory_compiler_root=root), _event("session-start"))

    assert result.ok is True
    assert result.exit_code == 0
    assert calls["command"] == [
        "uv",
        "run",
        "--directory",
        str(root),
        "python",
        str(hooks / "session-start.py"),
    ]
    assert calls["stdin"] == '{"session_id":"s1"}'
    assert result.stdout == "hook output\n"


def test_capture_delegates_to_session_end(tmp_path, monkeypatch):
    root = tmp_path / "memory-compiler"
    hooks = root / "hooks"
    hooks.mkdir(parents=True)
    (hooks / "session-end.py").write_text("print('ok')", encoding="utf-8")
    calls = {}

    def fake_run_process(command, stdin):
        calls["command"] = command
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr("memory_compiler_codex.lifecycle.run_process", fake_run_process)

    result = run_lifecycle(AdapterConfig(memory_compiler_root=root), _event("capture"))

    assert result.ok is True
    assert calls["command"][-1] == str(hooks / "session-end.py")


def test_process_failure_soft_fails_unless_strict(tmp_path, monkeypatch):
    root = tmp_path / "memory-compiler"
    hooks = root / "hooks"
    hooks.mkdir(parents=True)
    (hooks / "pre-compact.py").write_text("raise SystemExit(2)", encoding="utf-8")

    def fake_run_process(command, stdin):
        return subprocess.CompletedProcess(command, 2, stdout="", stderr="failed")

    monkeypatch.setattr("memory_compiler_codex.lifecycle.run_process", fake_run_process)

    soft = run_lifecycle(AdapterConfig(memory_compiler_root=root), _event("pre-compact"))
    strict = run_lifecycle(
        AdapterConfig(memory_compiler_root=root, strict=True),
        _event("pre-compact"),
    )

    assert soft.ok is True
    assert soft.exit_code == 0
    assert strict.ok is False
    assert strict.exit_code == 1
    assert strict.stderr == "failed"

