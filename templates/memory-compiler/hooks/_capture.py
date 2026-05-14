from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DAILY_DIR = ROOT / "daily"
KNOWLEDGE_DIR = ROOT / "knowledge"
MAX_TURNS = 30
MAX_CONTEXT_CHARS = 15_000


def read_hook_input() -> dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}
    return payload if isinstance(payload, dict) else {"value": payload}


def transcript_path_from(payload: dict[str, Any]) -> Path | None:
    path = payload.get("transcript_path") or payload.get("transcriptPath")
    if isinstance(path, str) and path:
        return Path(path)

    nested = payload.get("payload")
    if isinstance(nested, dict):
        return transcript_path_from(nested)
    return None


def extract_turns(transcript_path: Path) -> list[str]:
    turns: list[str] = []
    if not transcript_path.exists():
        return turns

    for line in transcript_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        message = entry.get("message") if isinstance(entry, dict) else None
        source = message if isinstance(message, dict) else entry
        if not isinstance(source, dict):
            continue

        role = source.get("role")
        content = source.get("content")
        text = text_content(content)
        if role in {"user", "assistant"} and text:
            label = "User" if role == "user" else "Assistant"
            turns.append(f"**{label}:** {text}")

    return turns[-MAX_TURNS:]


def text_content(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for item in content:
        if isinstance(item, str):
            parts.append(item)
        elif isinstance(item, dict) and item.get("type") == "text":
            text = item.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "\n".join(part.strip() for part in parts if part.strip())


def append_daily(event_name: str, payload: dict[str, Any]) -> None:
    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now(UTC).astimezone()
    daily_path = DAILY_DIR / f"{now:%Y-%m-%d}.md"
    transcript_path = transcript_path_from(payload)
    turns = extract_turns(transcript_path) if transcript_path else []
    body = "\n\n".join(turns)
    if len(body) > MAX_CONTEXT_CHARS:
        body = body[-MAX_CONTEXT_CHARS:]
    if not body:
        body = f"(no transcript turns captured; hook payload keys: {', '.join(sorted(payload)) or 'none'})"

    with daily_path.open("a", encoding="utf-8") as handle:
        handle.write(f"\n\n## [{now.isoformat()}] {event_name}\n\n{body}\n")
