from __future__ import annotations

from dataclasses import dataclass

from memory_compiler_codex.codex_hook_input import NormalizedCodexEvent
from memory_compiler_codex.config import AdapterConfig
from memory_compiler_codex.python_bridge import build_command, run_process


@dataclass(frozen=True)
class LifecycleResult:
    ok: bool
    exit_code: int
    message: str
    stdout: str = ""
    stderr: str = ""


def _failure(message: str, strict: bool) -> LifecycleResult:
    return LifecycleResult(ok=not strict, exit_code=1 if strict else 0, message=message)


def run_lifecycle(config: AdapterConfig, event: NormalizedCodexEvent) -> LifecycleResult:
    lifecycle = event.command

    if lifecycle == "post-tool-use":
        return LifecycleResult(ok=True, exit_code=0, message="post-tool-use skipped")

    if not config.memory_compiler_root.exists():
        return _failure(f"memory-compiler root missing: {config.memory_compiler_root}", config.strict)

    try:
        bridge_command = build_command(config.memory_compiler_root, lifecycle)
    except ValueError as exc:
        return _failure(str(exc), config.strict)

    if not bridge_command.script_path.exists():
        return _failure(f"memory-compiler hook script missing: {bridge_command.script_path}", config.strict)

    bridge_input = event.raw_payload if event.raw_payload and event.parse_error is None else event.to_json()
    process = run_process(bridge_command.command, bridge_input)
    if process.returncode != 0:
        result = _failure(
            f"memory-compiler hook failed for {lifecycle} with exit code {process.returncode}",
            config.strict,
        )
        return LifecycleResult(
            ok=result.ok,
            exit_code=result.exit_code,
            message=result.message,
            stdout=process.stdout,
            stderr=process.stderr,
        )

    return LifecycleResult(
        ok=True,
        exit_code=0,
        message=f"{lifecycle} delegated to memory-compiler",
        stdout=process.stdout,
        stderr=process.stderr,
    )
