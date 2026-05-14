from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from memory_compiler_codex.codex_hook_input import parse_hook_input
from memory_compiler_codex.config import resolve_config
from memory_compiler_codex.init_project import run_init
from memory_compiler_codex.lifecycle import run_lifecycle


COMMANDS = ("init", "session-start", "session-end", "pre-compact", "post-tool-use", "capture")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="memory-compiler-codex")
    parser.add_argument("command", choices=COMMANDS)
    parser.add_argument("--memory-compiler-root")
    parser.add_argument("--repo-root")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--strict", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        result = run_init(
            repo_root=Path(args.repo_root) if args.repo_root else None,
            memory_compiler_root=Path(args.memory_compiler_root)
            if args.memory_compiler_root
            else None,
            force=args.force,
        )
        print(result.message, file=sys.stderr)
        return result.exit_code

    stdin = "" if sys.stdin.isatty() else sys.stdin.read()
    config = resolve_config(
        cli_memory_compiler_root=args.memory_compiler_root,
        cli_strict=args.strict,
        env=os.environ,
    )
    event = parse_hook_input(args.command, stdin, os.environ)
    result = run_lifecycle(config, event)

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    print(result.message, file=sys.stderr)

    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
