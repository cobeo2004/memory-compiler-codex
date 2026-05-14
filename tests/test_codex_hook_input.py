from __future__ import annotations

import json

from memory_compiler_codex.codex_hook_input import parse_hook_input


def test_parse_json_stdin_preserves_raw_payload():
    raw = '{"session_id":"abc","transcript_path":"/tmp/transcript.jsonl"}'

    event = parse_hook_input("session-end", raw, {})

    assert event.command == "session-end"
    assert event.payload == {"session_id": "abc", "transcript_path": "/tmp/transcript.jsonl"}
    assert event.raw_payload == raw
    assert event.parse_error is None


def test_parse_non_object_json_wraps_value():
    event = parse_hook_input("session-start", '["value"]', {})

    assert event.payload == {"value": ["value"]}


def test_invalid_json_records_parse_error_and_raw_payload():
    event = parse_hook_input("pre-compact", "{bad", {})

    assert event.payload == {}
    assert event.raw_payload == "{bad"
    assert event.parse_error


def test_env_fallback_when_stdin_empty():
    event = parse_hook_input(
        "session-start",
        "",
        {
            "CODEX_SESSION_ID": "s1",
            "CODEX_TRANSCRIPT_PATH": "/tmp/t.jsonl",
            "CODEX_HOOK_EVENT_NAME": "SessionStart",
        },
    )

    assert event.payload == {
        "codex_session_id": "s1",
        "codex_transcript_path": "/tmp/t.jsonl",
        "codex_hook_event_name": "SessionStart",
    }


def test_to_json_contains_normalized_event():
    event = parse_hook_input("session-start", '{"session_id":"s1"}', {})

    data = json.loads(event.to_json())

    assert data["command"] == "session-start"
    assert data["payload"] == {"session_id": "s1"}
    assert data["raw_payload"] == '{"session_id":"s1"}'
    assert data["parse_error"] is None

