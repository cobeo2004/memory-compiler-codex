from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class InitResult:
    exit_code: int
    message: str
    warnings: tuple[str, ...] = field(default_factory=tuple)


def default_adapter_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_repo_root(adapter_root: Path) -> Path:
    if adapter_root.name == "memory-compiler-codex":
        return adapter_root.parent
    return Path.cwd()


def run_init(
    *,
    repo_root: Path | None = None,
    adapter_root: Path | None = None,
    memory_compiler_root: Path | None = None,
    force: bool = False,
) -> InitResult:
    adapter_root = (adapter_root or default_adapter_root()).resolve()
    repo_root = (repo_root or default_repo_root(adapter_root)).resolve()
    memory_compiler_root = _resolve_memory_compiler_root(
        repo_root=repo_root,
        adapter_root=adapter_root,
        memory_compiler_root=memory_compiler_root,
    )

    template_path = adapter_root / "templates" / "hooks.json"
    if not template_path.exists():
        return InitResult(1, f"hook template missing: {template_path}")

    warnings: list[str] = []
    repo_codex_dir = repo_root / ".codex"
    hooks_path = repo_codex_dir / "hooks.json"
    config_path = adapter_root / "config.json"
    starter_template = adapter_root / "templates" / "memory-compiler"

    repo_codex_dir.mkdir(parents=True, exist_ok=True)
    if not memory_compiler_root.exists() and starter_template.exists():
        shutil.copytree(starter_template, memory_compiler_root)

    try:
        template_hooks = _read_json_object(template_path)
        existing_hooks = _read_json_object(hooks_path) if hooks_path.exists() else {}
    except ValueError as exc:
        if not force:
            return InitResult(1, str(exc))
        existing_hooks = {}
        warnings.append(str(exc))

    merged_hooks = _merge_hook_config(existing_hooks, template_hooks)
    hooks_path.write_text(json.dumps(merged_hooks, indent=2) + "\n", encoding="utf-8")

    config = _read_json_object(config_path) if config_path.exists() else {}
    config["memoryCompilerRoot"] = _relative_or_absolute(memory_compiler_root, adapter_root)
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

    if not memory_compiler_root.exists():
        warnings.append(f"memory-compiler root does not exist yet: {memory_compiler_root}")

    suffix = "" if not warnings else f" ({'; '.join(warnings)})"
    return InitResult(0, f"initialized Codex memory hooks at {hooks_path}{suffix}", tuple(warnings))


def _resolve_memory_compiler_root(
    *,
    repo_root: Path,
    adapter_root: Path,
    memory_compiler_root: Path | None,
) -> Path:
    if memory_compiler_root is None:
        return (repo_root / "memory-compiler").resolve()
    if memory_compiler_root.is_absolute():
        return memory_compiler_root.resolve()
    return (repo_root / memory_compiler_root).resolve()


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object in {path}")
    return data


def _merge_hook_config(existing: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    merged = dict(existing)
    existing_hooks = _hook_map(merged)
    template_hooks = _hook_map(template)
    output_hooks = dict(existing_hooks)

    for event_name, template_entries in template_hooks.items():
        current_entries = list(output_hooks.get(event_name, []))
        current_commands = _commands_for_entries(current_entries)
        for entry in template_entries:
            if _entry_commands(entry).isdisjoint(current_commands):
                current_entries.append(entry)
                current_commands.update(_entry_commands(entry))
        output_hooks[event_name] = current_entries

    merged["hooks"] = output_hooks
    return merged


def _hook_map(config: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    hooks = config.get("hooks")
    if not isinstance(hooks, dict):
        return {}

    result: dict[str, list[dict[str, Any]]] = {}
    for event_name, entries in hooks.items():
        if isinstance(event_name, str) and isinstance(entries, list):
            result[event_name] = [entry for entry in entries if isinstance(entry, dict)]
    return result


def _commands_for_entries(entries: list[dict[str, Any]]) -> set[str]:
    commands: set[str] = set()
    for entry in entries:
        commands.update(_entry_commands(entry))
    return commands


def _entry_commands(entry: dict[str, Any]) -> set[str]:
    hooks = entry.get("hooks")
    if not isinstance(hooks, list):
        return set()
    commands: set[str] = set()
    for hook in hooks:
        if isinstance(hook, dict) and isinstance(hook.get("command"), str):
            commands.add(hook["command"])
    return commands


def _relative_or_absolute(path: Path, base: Path) -> str:
    try:
        return os.path.relpath(path, base)
    except ValueError:
        return str(path)
