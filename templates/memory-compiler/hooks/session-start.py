from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT / "knowledge"
DAILY_DIR = ROOT / "daily"
MAX_CONTEXT_CHARS = 20_000
MAX_LOG_LINES = 30


def recent_log() -> str:
    today = datetime.now(UTC).astimezone()
    for offset in range(2):
        path = DAILY_DIR / f"{today - timedelta(days=offset):%Y-%m-%d}.md"
        if path.exists():
            lines = path.read_text(encoding="utf-8").splitlines()
            return "\n".join(lines[-MAX_LOG_LINES:])
    return "(no recent daily log)"


def build_context() -> str:
    index_path = KNOWLEDGE_DIR / "index.md"
    index = index_path.read_text(encoding="utf-8") if index_path.exists() else "# Knowledge Index\n\nEmpty."
    context = "\n\n---\n\n".join(
        [
            f"## Today\n{datetime.now(UTC).astimezone():%A, %B %d, %Y}",
            f"## Knowledge Base Index\n\n{index}",
            f"## Recent Daily Log\n\n{recent_log()}",
        ]
    )
    return context[:MAX_CONTEXT_CHARS]


def main() -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": build_context(),
                }
            }
        )
    )


if __name__ == "__main__":
    main()
