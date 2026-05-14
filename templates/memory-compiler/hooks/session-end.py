from __future__ import annotations

from _capture import append_daily, read_hook_input


def main() -> None:
    append_daily("SessionEnd", read_hook_input())


if __name__ == "__main__":
    main()
