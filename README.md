# Memory Compiler Codex

`memory-compiler-codex` is a copyable Codex memory kit. It contains:

- a Python Codex hook adapter
- Codex hook templates
- a starter `memory-compiler/` template for people who do not already know or
  have the original memory compiler

The adapter normalises Codex hook input, resolves the memory-compiler root, and
delegates to Python hook scripts with predictable fallbacks.

## What it does

- Initializes a fresh repo with `.codex/hooks.json` and `memory-compiler/`.
- Bridges Codex hook events to `memory-compiler` lifecycle scripts.
- Keeps the compiler portable through `MEMORY_COMPILER_ROOT`, so the adapter can
  point at a sibling checkout or any other location.
- Soft-fails by default when the memory-compiler root or hook script is missing.
- Supports strict mode when you want hook failures to exit non-zero.

## Setup

Copy only this directory into the target repo:

```text
target-repo/
  memory-compiler-codex/
```

Then initialize the target repo from the target repo root:

```bash
uv run --directory ./memory-compiler-codex python -m memory_compiler_codex init
```

`init` writes or merges `.codex/hooks.json` and writes
`memory-compiler-codex/config.json`. If `memory-compiler/` does not exist yet,
it creates one from `memory-compiler-codex/templates/memory-compiler/`.

If the target repo already has a compiler somewhere else:

```bash
uv run --directory ./memory-compiler-codex python -m memory_compiler_codex init \
  --memory-compiler-root /absolute/path/to/memory-compiler
```

It is safe to run `init` again. Existing hook commands are preserved, adapter
hook commands are not duplicated, and an existing `memory-compiler/` is left in
place.

To install dependencies directly:

```bash
cd memory-compiler-codex
uv sync
```

The default env template assumes a repo-local compiler created by `init`:

```bash
cp templates/env.example .env
```

If the compiler lives elsewhere, point `MEMORY_COMPILER_ROOT` at that path.

## Hook template

`templates/hooks.json` mirrors the Codex hook shape used by `.codex/hooks.json`
and wires these commands through the adapter:

- `session-start`
- `session-end`
- `pre-compact`
- `post-tool-use`
- `capture`

The adapter currently skips `post-tool-use` work, but the hook entry is present
so the surface stays ready if that lifecycle becomes useful later.

## What `init` creates

```text
target-repo/
  .codex/hooks.json
  memory-compiler/
    hooks/
      session-start.py
      session-end.py
      pre-compact.py
    daily/
    knowledge/
    scripts/compile.py
  memory-compiler-codex/config.json
```

The starter compiler captures transcript turns into daily logs and can rebuild a
basic `knowledge/index.md`. It does not require an external SDK. You can replace
it later with a fuller compiler as long as the same hook script names remain.

## Commands

- `session-start` - delegate the Codex SessionStart hook.
- `session-end` - delegate the Codex Stop hook.
- `pre-compact` - delegate the Codex PreCompact hook.
- `post-tool-use` - accepted by the CLI, currently soft-skipped by lifecycle.
- `capture` - manual alias for the session-end bridge path.
- `init` - bootstrap `.codex/hooks.json` and `memory-compiler-codex/config.json`
  in a target repo.

Run them from the repo root with `uv`:

```bash
uv run --directory ./memory-compiler-codex python -m memory_compiler_codex session-start
uv run --directory ./memory-compiler-codex python -m memory_compiler_codex session-end
uv run --directory ./memory-compiler-codex python -m memory_compiler_codex pre-compact
uv run --directory ./memory-compiler-codex python -m memory_compiler_codex post-tool-use
uv run --directory ./memory-compiler-codex python -m memory_compiler_codex capture
uv run --directory ./memory-compiler-codex python -m memory_compiler_codex init
```

## Environment

- `MEMORY_COMPILER_ROOT=../memory-compiler`
- `MEMORY_COMPILER_CODEX_STRICT=0`

Set `MEMORY_COMPILER_CODEX_STRICT=1` when you want missing roots, missing hook
scripts, or hook process failures to exit with code 1 instead of soft-failing.

## Optional future companion

`@openai/codex-sdk` is not required for this adapter. It only becomes relevant
if Codex hook data ever becomes richer than the current stdin contract and the
adapter needs an additional companion layer.

## Verification

```bash
cd memory-compiler-codex
uv run pytest tests/test_cli_integration.py
python -m json.tool templates/hooks.json >/dev/null
uv run ruff check src tests
```
