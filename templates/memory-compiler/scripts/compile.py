from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DAILY_DIR = ROOT / "daily"
KNOWLEDGE_DIR = ROOT / "knowledge"
INDEX_FILE = KNOWLEDGE_DIR / "index.md"
LOG_FILE = KNOWLEDGE_DIR / "log.md"


def main() -> None:
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    daily_logs = sorted(DAILY_DIR.glob("*.md")) if DAILY_DIR.exists() else []
    lines = ["# Knowledge Index", ""]
    if daily_logs:
        lines.append("## Daily Logs")
        lines.extend(f"- [[daily/{path.name}]]" for path in daily_logs)
    else:
        lines.append("No daily logs captured yet.")
    INDEX_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## [{datetime.now(UTC).astimezone().isoformat()}] compile\n")
        handle.write(f"- Daily logs indexed: {len(daily_logs)}\n")

    print(f"indexed {len(daily_logs)} daily logs")


if __name__ == "__main__":
    main()
