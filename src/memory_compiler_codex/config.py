from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


TRUTHY_VALUES = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AdapterConfig:
    memory_compiler_root: Path
    strict: bool = False


def _truthy(value: str | None) -> bool:
    return value is not None and value.strip().lower() in TRUTHY_VALUES


def _read_config_file(adapter_root: Path) -> dict[str, object]:
    config_path = adapter_root / "config.json"
    if not config_path.exists():
        return {}

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    return data if isinstance(data, dict) else {}


def _default_memory_compiler_root(adapter_root: Path) -> Path:
    local_default = adapter_root / "memory-compiler"
    if local_default.exists():
        return local_default
    return adapter_root.parent / "memory-compiler"


def resolve_config(
    *,
    cli_memory_compiler_root: str | Path | None = None,
    cli_strict: bool = False,
    env: Mapping[str, str] | None = None,
    adapter_root: str | Path | None = None,
) -> AdapterConfig:
    env = env or os.environ
    root = Path(adapter_root) if adapter_root is not None else Path.cwd()
    file_config = _read_config_file(root)

    configured_root = (
        cli_memory_compiler_root
        or env.get("MEMORY_COMPILER_ROOT")
        or env.get("CODEX_MEMORY_COMPILER_ROOT")
        or file_config.get("memoryCompilerRoot")
    )

    if configured_root:
        memory_compiler_root = Path(str(configured_root)).expanduser()
    else:
        memory_compiler_root = _default_memory_compiler_root(root)

    if not memory_compiler_root.is_absolute():
        memory_compiler_root = root / memory_compiler_root

    strict = (
        cli_strict
        or _truthy(env.get("MEMORY_COMPILER_CODEX_STRICT"))
        or bool(file_config.get("strict"))
    )

    return AdapterConfig(memory_compiler_root=memory_compiler_root.resolve(), strict=strict)

