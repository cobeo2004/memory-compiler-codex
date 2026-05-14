from __future__ import annotations

import json
from pathlib import Path

from memory_compiler_codex.init_project import run_init


def _write_template(adapter_root: Path) -> None:
    templates = adapter_root / "templates"
    templates.mkdir(parents=True)
    (templates / "hooks.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": "",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "uv run --directory ./memory-compiler-codex python -m memory_compiler_codex session-start",
                                    "timeout": 15,
                                }
                            ],
                        }
                    ],
                    "Stop": [
                        {
                            "matcher": "",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "uv run --directory ./memory-compiler-codex python -m memory_compiler_codex session-end",
                                    "timeout": 15,
                                }
                            ],
                        }
                    ],
                }
            }
        ),
        encoding="utf-8",
    )
    memory_template = adapter_root / "templates" / "memory-compiler"
    (memory_template / "hooks").mkdir(parents=True)
    (memory_template / "hooks" / "session-start.py").write_text("", encoding="utf-8")
    (memory_template / "hooks" / "session-end.py").write_text("", encoding="utf-8")
    (memory_template / "hooks" / "pre-compact.py").write_text("", encoding="utf-8")


def test_init_writes_hooks_and_adapter_config(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    adapter_root = repo_root / "memory-compiler-codex"
    memory_root = repo_root / "memory-compiler"
    memory_root.mkdir(parents=True)
    _write_template(adapter_root)

    result = run_init(repo_root=repo_root, adapter_root=adapter_root)

    assert result.exit_code == 0
    hooks = json.loads((repo_root / ".codex" / "hooks.json").read_text(encoding="utf-8"))
    config = json.loads((adapter_root / "config.json").read_text(encoding="utf-8"))
    assert hooks["hooks"]["SessionStart"][0]["hooks"][0]["command"].endswith("session-start")
    assert config["memoryCompilerRoot"] == "../memory-compiler"


def test_init_merges_existing_hooks_without_duplicates(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    adapter_root = repo_root / "memory-compiler-codex"
    memory_root = repo_root / "memory-compiler"
    codex_dir = repo_root / ".codex"
    memory_root.mkdir(parents=True)
    codex_dir.mkdir(parents=True)
    _write_template(adapter_root)
    (codex_dir / "hooks.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": "",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "existing session command",
                                }
                            ],
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    first = run_init(repo_root=repo_root, adapter_root=adapter_root)
    second = run_init(repo_root=repo_root, adapter_root=adapter_root)

    assert first.exit_code == 0
    assert second.exit_code == 0
    hooks = json.loads((codex_dir / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    session_commands = [
        hook["command"]
        for entry in hooks["SessionStart"]
        for hook in entry["hooks"]
    ]
    assert session_commands.count("existing session command") == 1
    assert (
        session_commands.count(
            "uv run --directory ./memory-compiler-codex python -m memory_compiler_codex session-start"
        )
        == 1
    )
    assert "Stop" in hooks


def test_init_creates_memory_compiler_when_missing(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    adapter_root = repo_root / "memory-compiler-codex"
    adapter_root.mkdir(parents=True)
    _write_template(adapter_root)

    result = run_init(repo_root=repo_root, adapter_root=adapter_root)

    assert result.exit_code == 0
    assert result.warnings == ()
    assert (repo_root / "memory-compiler" / "hooks" / "session-start.py").exists()


def test_init_warns_when_memory_compiler_template_is_missing(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    adapter_root = repo_root / "memory-compiler-codex"
    (adapter_root / "templates").mkdir(parents=True)
    (adapter_root / "templates" / "hooks.json").write_text(
        json.dumps({"hooks": {}}),
        encoding="utf-8",
    )

    result = run_init(repo_root=repo_root, adapter_root=adapter_root)

    assert result.exit_code == 0
    assert result.warnings
    assert "does not exist yet" in result.warnings[0]
