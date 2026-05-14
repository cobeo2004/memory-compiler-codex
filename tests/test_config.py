from __future__ import annotations

import json

from memory_compiler_codex.config import resolve_config


def test_cli_root_takes_precedence(tmp_path):
    adapter_root = tmp_path / "adapter"
    adapter_root.mkdir()
    cli_root = tmp_path / "cli-memory"

    config = resolve_config(
        cli_memory_compiler_root=cli_root,
        env={
            "MEMORY_COMPILER_ROOT": str(tmp_path / "env-memory"),
            "CODEX_MEMORY_COMPILER_ROOT": str(tmp_path / "codex-env-memory"),
        },
        adapter_root=adapter_root,
    )

    assert config.memory_compiler_root == cli_root.resolve()


def test_env_precedence_before_codex_env_and_config_file(tmp_path):
    adapter_root = tmp_path / "adapter"
    adapter_root.mkdir()
    (adapter_root / "config.json").write_text(
        json.dumps({"memoryCompilerRoot": "file-memory", "strict": True}),
        encoding="utf-8",
    )
    env_root = tmp_path / "env-memory"

    config = resolve_config(
        env={
            "MEMORY_COMPILER_ROOT": str(env_root),
            "CODEX_MEMORY_COMPILER_ROOT": str(tmp_path / "codex-env-memory"),
        },
        adapter_root=adapter_root,
    )

    assert config.memory_compiler_root == env_root.resolve()
    assert config.strict is True


def test_defaults_to_local_memory_compiler_then_sibling(tmp_path):
    adapter_root = tmp_path / "memory-compiler-codex"
    local_default = adapter_root / "memory-compiler"
    local_default.mkdir(parents=True)

    local_config = resolve_config(env={}, adapter_root=adapter_root)

    assert local_config.memory_compiler_root == local_default.resolve()

    local_default.rmdir()
    sibling_default = tmp_path / "memory-compiler"

    sibling_config = resolve_config(env={}, adapter_root=adapter_root)

    assert sibling_config.memory_compiler_root == sibling_default.resolve()


def test_strict_from_cli_env_or_config(tmp_path):
    adapter_root = tmp_path / "adapter"
    adapter_root.mkdir()

    assert resolve_config(cli_strict=True, env={}, adapter_root=adapter_root).strict is True
    assert (
        resolve_config(
            env={"MEMORY_COMPILER_CODEX_STRICT": "yes"},
            adapter_root=adapter_root,
        ).strict
        is True
    )

