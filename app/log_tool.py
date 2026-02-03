# log_tool.py
# CLI entrypoint for log-tool.
#
# Commands:
#   python3 log_tool.py log <ItemName> <Value> [-YYYY-MM-DD]
#   python3 log_tool.py show [YYYY-MM-DD]
#   python3 log_tool.py history [N]
#   python3 log_tool.py version

import sys

from config import VERSION
from events import log_event, show_history
from groups import log_item, show_day


def main() -> None:
    args = sys.argv[1:]

    try:
        # Log the raw command-line invocation
        log_event(f"CMD args={args!r}")

        # Basic command-line parsing
        if len(args) == 0:
            msg = (
                "Usage:\n"
                "  python3 log_tool.py log <ItemName> <Value> [-YYYY-MM-DD]\n"
                "  python3 log_tool.py show [YYYY-MM-DD]\n"
                "  python3 log_tool.py history [N]\n"
                "  python3 log_tool.py version"
            )
            print(msg)
            log_event("INFO printed usage (no arguments)")
            return

        command = args[0]

        if command == "log":
            if len(args) not in (3, 4):
                msg = "Usage: python3 log_tool.py log <ItemName> <Value> [-YYYY-MM-DD]"
                print(msg)
                log_event(f"ERROR {msg}")
                return

            _, item_name, value_str = args[0:3]
            log_date = None

            if len(args) == 4:
                date_flag = args[3]  # expects something like -2026-02-01
                if not date_flag.startswith("-"):
                    msg = "Date flag must start with '-' and use YYYY-MM-DD, e.g. -2026-02-01"
                    print(msg)
                    log_event(f"ERROR {msg}")
                    return
                log_date = date_flag[1:]  # strip the leading '-'
                # (Optional) validate format here with datetime.date.fromisoformat

            log_item(item_name, value_str, log_date=log_date)

        elif command == "show":
            # Usage:
            #   python3 log_tool.py show             -> show today's data across groups
            #   python3 log_tool.py show 2026-02-01  -> show data for that date
            if len(args) == 1:
                show_day()
            elif len(args) == 2:
                log_date = args[1]
                # (Optional) validate date format here
                show_day(log_date)
            else:
                msg = "Usage: python3 log_tool.py show [YYYY-MM-DD]"
                print(msg)
                log_event(f"ERROR {msg}")

        elif command == "history":
            # Usage:
            #   python3 log_tool.py history       -> last 10 events
            #   python3 log_tool.py history 20    -> last 20 events
            if len(args) == 1:
                show_history()
            elif len(args) == 2:
                try:
                    n = int(args[1])
                    if n <= 0:
                        raise ValueError
                except ValueError:
                    msg = "history N requires a positive integer N, e.g. 'history 20'."
                    print(msg)
                    log_event(f"ERROR {msg}")
                    return
                show_history(n)
            else:
                msg = "Usage: python3 log_tool.py history [N]"
                print(msg)
                log_event(f"ERROR {msg}")

        elif command == "version":
            msg = f"log-tool {VERSION}"
            print(msg)
            log_event(f"INFO version {VERSION} printed")

        else:
            msg = (
                f"Unknown command: {command!r}. "
                "For now we support 'log', 'show', 'history', and 'version'."
            )
            print(msg)
            log_event(f"ERROR {msg}")

    except Exception as e:
        # Catch anything unexpected so it also lands in log.txt
        err_msg = f"log-tool: ERROR {type(e).__name__}: {e}"
        log_event(err_msg)
        print(err_msg)


if __name__ == "__main__":
    main()
