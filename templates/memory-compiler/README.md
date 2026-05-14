# LLM Personal Knowledge Base

**Your Codex conversations compile themselves into a searchable knowledge base.**

Adapted from [Karpathy's LLM Knowledge Base](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) architecture, but instead of clipping web articles, the raw data is your own conversations with Codex. When a session ends or compacts mid-session, Codex hooks call `memory-compiler-codex`, which delegates to the hook scripts in this directory. The starter captures useful transcript turns into `daily/YYYY-MM-DD.md`; `scripts/compile.py` rebuilds a basic markdown index from those daily logs. Retrieval uses a simple index file instead of RAG - no vector database, no embeddings, just markdown.

This starter is intentionally local and dependency-light. It works without an external SDK or API key. If you later replace it with a fuller compiler, keep the same hook script names so `memory-compiler-codex` can continue calling it.

## Quick Start

Copy `memory-compiler-codex/` into a fresh project and run:

```bash
uv run --directory ./memory-compiler-codex python -m memory_compiler_codex init
```

The init command will:

1. Create this `memory-compiler/` directory if it does not already exist.
2. Create or merge `.codex/hooks.json`.
3. Write `memory-compiler-codex/config.json` so the adapter points back here.

From there, Codex hook events can start accumulating daily logs. You can also run `uv run --directory ./memory-compiler python scripts/compile.py` manually at any time.

## How It Works

```text
Conversation -> Codex SessionEnd/PreCompact hooks -> memory-compiler-codex
    -> hooks/session-end.py or hooks/pre-compact.py -> daily/YYYY-MM-DD.md
        -> scripts/compile.py -> knowledge/index.md
            -> hooks/session-start.py injects the index into the next session
```

- **Codex hooks** capture conversations automatically through the adapter.
- **session-end.py** and **pre-compact.py** append transcript turns to daily logs.
- **compile.py** rebuilds `knowledge/index.md` from captured daily logs.
- **session-start.py** injects the current index and recent daily log into new sessions.
- The starter keeps all state in markdown and local files.

## Key Commands

Run from the target repository root:

```bash
uv run --directory ./memory-compiler-codex python -m memory_compiler_codex init
uv run --directory ./memory-compiler-codex python -m memory_compiler_codex session-start
uv run --directory ./memory-compiler-codex python -m memory_compiler_codex session-end
uv run --directory ./memory-compiler-codex python -m memory_compiler_codex pre-compact
uv run --directory ./memory-compiler python scripts/compile.py
```

## Why No RAG?

Karpathy's insight: at personal scale (50-500 articles), the LLM reading a structured `index.md` outperforms vector similarity. The LLM understands what you're really asking; cosine similarity just finds similar words. RAG becomes necessary at larger scale when the index exceeds the context window.

## Technical Reference

See **[AGENTS.md](AGENTS.md)** for the complete technical reference: article formats, hook architecture, script internals, cross-platform details, and customization options. AGENTS.md is designed to give an AI agent everything it needs to understand, modify, or rebuild the system.
