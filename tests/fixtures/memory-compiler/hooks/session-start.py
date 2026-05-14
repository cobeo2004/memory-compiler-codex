from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    output = os.environ.get("FAKE_MEMORY_COMPILER_OUT")
    if not output:
        return 0

    payload = sys.stdin.read()
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(payload)
        if payload and not payload.endswith("\n"):
            handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
