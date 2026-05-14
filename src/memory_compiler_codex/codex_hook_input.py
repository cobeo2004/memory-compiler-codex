from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class NormalizedCodexEvent:
    command: str
    payload: dict[str, Any] = field(default_factory=dict)
    raw_payload: str = ""
    parse_error: str | None = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "command": self.command,
                "payload": self.payload,
                "raw_payload": self.raw_payload,
                "parse_error": self.parse_error,
            },
            separators=(",", ":"),
        )


def parse_hook_input(command: str, stdin: str, env: Mapping[str, str]) -> NormalizedCodexEvent:
    raw_payload = stdin.strip()
    if raw_payload:
        try:
            parsed = json.loads(raw_payload)
        except json.JSONDecodeError as exc:
            return NormalizedCodexEvent(
                command=command,
                payload={},
                raw_payload=raw_payload,
                parse_error=str(exc),
            )

        payload = parsed if isinstance(parsed, dict) else {"value": parsed}
        return NormalizedCodexEvent(command=command, payload=payload, raw_payload=raw_payload)

    payload: dict[str, Any] = {}
    for key in ("CODEX_SESSION_ID", "CODEX_TRANSCRIPT_PATH", "CODEX_HOOK_EVENT_NAME"):
        if key in env:
            payload[key.lower()] = env[key]

    return NormalizedCodexEvent(command=command, payload=payload, raw_payload="")

