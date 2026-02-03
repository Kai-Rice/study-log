# events.py
# Event logging (log.txt) and history viewing.

from datetime import datetime, timezone

from config import LOG_FILE


def log_event(message: str) -> None:
    """
    Append a timestamped event line to log.txt.
    """
    # timezone-aware UTC timestamp
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    # Normalize "+00:00" to "Z" for nicer display
    if timestamp.endswith("+00:00"):
        timestamp = timestamp[:-6] + "Z"

    line = f"{timestamp} {message}\n"
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line)


def show_history(limit: int = 10) -> None:
    """
    Print the last `limit` lines from log.txt (most recent events).
    """
    if not LOG_FILE.exists():
        print(f"log-tool: No history yet (log file {LOG_FILE.name} does not exist).")
        return

    with LOG_FILE.open("r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    if not lines:
        print(f"log-tool: History is empty in {LOG_FILE.name}.")
        return

    tail = lines[-limit:]

    print(f"log-tool: Last {len(tail)} event(s) from {LOG_FILE.name}:\n")
    for line in tail:
        print(line)
