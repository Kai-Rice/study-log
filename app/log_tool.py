# log-tool v0.7.0

from pathlib import Path
from datetime import date, datetime, timezone
import csv
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR   = SCRIPT_DIR.parent
DATA_DIR   = ROOT_DIR / "data"
STUDY_FILE = DATA_DIR / "study.csv" # STUDY_FILE points to ~log-tool/data/study.csv
LOG_FILE  = SCRIPT_DIR / "log.txt"


def today_iso() -> str: # returns today's date as an ISO-formatted string (YYYY-MM-DD)
    return date.today().isoformat()


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


def list_group_files() -> list[Path]:
    """
    Return a sorted list of all .csv files under DATA_DIR.
    Each file is treated as a 'group' CSV.
    """
    if not DATA_DIR.exists():
        raise RuntimeError(f"Data directory not found: {DATA_DIR}")

    files = [p for p in DATA_DIR.glob("*.csv") if p.is_file()]
    if not files:
        raise RuntimeError(f"No group CSV files found in {DATA_DIR}")
    return sorted(files)


def load_group_csv(group_file: Path):
    """
    Load a specific group CSV and return (headers, types, rows).
    """
    if not group_file.exists():
        raise RuntimeError(f"Group CSV not found: {group_file}")

    with group_file.open("r", newline="", encoding="utf-8") as f:
        reader = list(csv.reader(f))

    if len(reader) < 2:
        raise RuntimeError(f"{group_file.name} must have at least 2 rows (header + types).")

    headers = reader[0]
    types   = reader[1]
    rows    = reader[2:]
    return headers, types, rows


def save_group_csv(group_file: Path, headers, types, rows) -> None:
    """
    Save (headers, types, rows) back to the given group CSV.
    """
    with group_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerow(types)
        writer.writerows(rows)


def load_study_csv():

    # 1) Check whether the file exists on disk.
    # .exists() returns True/False
    if not STUDY_FILE.exists():
        raise RuntimeError(f"study.csv not found at {STUDY_FILE}")
    
    # 2) Open the file safely using a context manager ("with")
    # This guarantees the file is closed automatically when we leave this block.
    #
    # "r" = read mode
    # encoding="utf-8" = read as UTF-8 text
    # newline="" = handle newlines correctly for CSV files
    with STUDY_FILE.open("r", newline="", encoding="utf-8") as f: # opens file, read it as CSV, store all rows in memory.
        # csv.reader(f) reads the file line-by-line and splits each line by commas,
        # producing rows like: ["2026-02-01", "45", "math"]
        #
        # list(...) consumes the reader iterator and stores ALL rows in memory.
        reader = list(csv.reader(f))
    
    # 3) Basic validation: we expect at least the header and type rows
    if len(reader) < 2:
        raise RuntimeError("study.csv must have at least 2 rows (header + types).")
    
    headers = reader[0] # first row
    types   = reader[1] # second row
    rows    = reader[2:] # everything after the first two rows
    
    return headers, types, rows


def save_study_csv(headers, types, rows): # the arguments are what the function will write to the file

    # opens STUDY_FILE for writing (overwrites existing file)
    with STUDY_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f) # creates a CSV writer object
        writer.writerow(headers) # writes (one) header row
        writer.writerow(types) # writes (one) types row
        writer.writerows(rows) # writes all data rows


def find_column(headers, name): # finds the index of a column by name

    try:
        return headers.index(name)
    
    except ValueError: # raised if name not found in headers
        raise RuntimeError(f"Column {name!r} not found in study.csv.")


def validate_integer(value_str: str) -> int: # validates that a string can be converted to an integer
    try:
        parsed_int = int(value_str) # try to convert the string to an integer
    except ValueError:
        raise ValueError("Value must be an integer.") # raise a new error if conversion fails
    return parsed_int # return the parsed integer


def is_na_input(value_str: str) -> bool:
    """
    Return True if the user explicitly wants to set this cell to N/A.
    """
    s = value_str.strip().lower()
    return s in ("na", "n/a")


def validate_boolean(value_str: str) -> str:
    """
    Validate a boolean input and return 'TRUE' or 'FALSE'.

    Accepted (case-insensitive):
      - truthy:  t, true, y, yes, 1
      - falsy:   f, false, n, no, 0
    """
    s = value_str.strip().lower()

    truthy = {"t", "true", "y", "yes", "1"}
    falsy  = {"f", "false", "n", "no", "0"}

    if s in truthy:
        return "TRUE"
    if s in falsy:
        return "FALSE"

    raise ValueError(
        "Boolean value must be one of: t/f, true/false, y/n, yes/no, 1/0."
    )


def validate_int_range(value_str: str) -> int:
    """
    Validate a 1–10 rating (int_range). Return the integer value.

    - Must be an integer
    - Must be between 1 and 10 (inclusive)
    """
    try:
        value_int = int(value_str)
    except ValueError:
        raise ValueError("int_range value must be an integer between 1 and 10.")

    if not 1 <= value_int <= 10:
        raise ValueError("int_range value must be between 1 and 10.")

    return value_int


def parse_duration_to_seconds(value_str: str) -> int:
    """
    Parse a duration string into total seconds.

    Accepted formats:
      - "mm:ss"
      - "hh:mm:ss"

    Examples:
      "30:00"    -> 1800
      "01:15:30" -> 4530
    """
    parts = value_str.split(":")

    if len(parts) == 2:
        # mm:ss
        mm_str, ss_str = parts
        hh = 0
        mm = int(mm_str)
        ss = int(ss_str)
    elif len(parts) == 3:
        # hh:mm:ss
        hh_str, mm_str, ss_str = parts
        hh = int(hh_str)
        mm = int(mm_str)
        ss = int(ss_str)
    else:
        raise ValueError(
            "Duration must be in mm:ss or hh:mm:ss format, "
            f"got {value_str!r}"
        )

    if mm < 0 or mm >= 60 or ss < 0 or ss >= 60 or hh < 0:
        raise ValueError(f"Invalid duration components in {value_str!r}")

    return hh * 3600 + mm * 60 + ss


def format_seconds_as_duration(total_seconds: int) -> str:
    """
    Format total seconds as 'hh:mm:ss'.
    """
    if total_seconds < 0:
        raise ValueError("Duration cannot be negative.")

    hh = total_seconds // 3600
    remainder = total_seconds % 3600
    mm = remainder // 60
    ss = remainder % 60

    return f"{hh:02d}:{mm:02d}:{ss:02d}"


def find_item_location(item_name: str):
    """
    Search all group CSV files under DATA_DIR for a column named `item_name`.

    Returns a tuple:
      (group_file, headers, types, rows, item_col, log_date_col)

    - group_file   : Path to the CSV file for that group
    - headers      : header row list
    - types        : type row list
    - rows         : data rows list
    - item_col     : index of the item column
    - log_date_col : index of the 'Log_Date' column

    For now, we require that item names are unique across all groups.
    """
    matches = []

    for group_file in list_group_files():
        headers, types, rows = load_group_csv(group_file)

        if item_name in headers:
            item_col = headers.index(item_name)
            try:
                log_date_col = headers.index("Log_Date")
            except ValueError:
                raise RuntimeError(f"{group_file.name} has no 'Log_Date' column.")

            matches.append((group_file, headers, types, rows, item_col, log_date_col))

    if not matches:
        raise RuntimeError(
            f"Item {item_name!r} not found in any group CSV in {DATA_DIR}."
        )

    if len(matches) > 1:
        details = ", ".join(
            f"{m[0].name} (col {m[4]})" for m in matches
        )
        raise RuntimeError(
            f"Item {item_name!r} found in multiple group files: {details}. "
            "This version requires item names to be unique across all groups."
        )

    return matches[0]


def log_item(item_name: str, value_str: str, log_date: str | None = None) -> None:
    """
    Log a value for the given item_name on the given log_date.

    - Searches across all group CSVs in DATA_DIR to find the column.
    - Requires item names to be unique across all groups (for now).

    Supported types:
      - integer   (SET behavior)
      - duration  (ADD behavior, stored as hh:mm:ss)
      - boolean   (SET behavior, stored as TRUE/FALSE)
      - int_range (SET behavior, 1–10)

    Special input:
      - 'na' / 'n/a' sets the cell to 'N/A' regardless of type (for now).

    If log_date is None, use today's date.
    """
    # 1) Decide which date to log to
    if log_date is None:
        log_date = today_iso()

    # 2) Find which group + column this item belongs to
    (
        group_file,
        headers,
        types,
        rows,
        item_col,
        log_date_col,
    ) = find_item_location(item_name)

    group_name = group_file.stem

    # 3) Look up the item type
    item_type = types[item_col]

    # 4) Find or create the row for this log_date
    target_row = None

    for row in rows:
        # Ensure row has enough columns (defensive)
        if len(row) < len(headers):
            row.extend([""] * (len(headers) - len(row)))

        if row[log_date_col] == log_date:
            target_row = row
            break

    if target_row is None:
        # No row for this date yet → create one
        target_row = [""] * len(headers)
        target_row[log_date_col] = log_date
        rows.append(target_row)

    # 5) Handle 'na' / 'n/a' input first (applies to any type)
    if is_na_input(value_str):
        previous = target_row[item_col] or "N/A"
        value    = "N/A"
        target_row[item_col] = value

    # 6) Dispatch based on type
    elif item_type == "integer":
        # integer behavior: SET
        value_int = validate_integer(value_str)
        value     = str(value_int)

        previous = target_row[item_col] or "N/A"
        target_row[item_col] = value

    elif item_type == "duration":
        # Duration behavior: ADD to existing
        added_seconds = parse_duration_to_seconds(value_str)

        existing_str = target_row[item_col].strip() if target_row[item_col] else ""
        if existing_str and existing_str != "N/A":
            try:
                existing_seconds = parse_duration_to_seconds(existing_str)
            except ValueError:
                # If the existing data is bad, treat as 0 for now
                existing_seconds = 0
        else:
            existing_seconds = 0

        new_total_seconds = existing_seconds + added_seconds
        previous = format_seconds_as_duration(existing_seconds)
        value    = format_seconds_as_duration(new_total_seconds)

        target_row[item_col] = value

    elif item_type == "boolean":
        # Boolean behavior: SET, stored as TRUE/FALSE
        value = validate_boolean(value_str)
        previous = target_row[item_col] or "N/A"
        target_row[item_col] = value

    elif item_type == "int_range":
        # int_range behavior: SET, 1–10
        value_int = validate_int_range(value_str)
        value     = str(value_int)
        previous = target_row[item_col] or "N/A"
        target_row[item_col] = value

    else:
        raise RuntimeError(
            f"Column {item_name!r} in group {group_name!r} has unsupported type {item_type!r} "
            "(supported: integer, duration, boolean, int_range)"
        )

    # 7) Save changes back to disk (to that specific group file)
    save_group_csv(group_file, headers, types, rows)

    # 8) Log + feedback
    msg = (
        f"log-tool: Updated {item_name} in group {group_name} for {log_date}: "
        f"(prev: {previous}) -> {value}"
    )
    log_event(msg)
    print(msg)


def show_day(log_date: str | None = None) -> None:
    """
    Show the data rows for a given log_date across all group CSVs.

    - If log_date is None, use today's date.
    - For each group, only prints columns that have a non-empty value.
    - Output is grouped by [Group: name], with vertical "Name: Value" lines.
    """
    if log_date is None:
        log_date = today_iso()

    groups_with_data: list[tuple[str, list[tuple[str, str]]]] = []

    for group_file in list_group_files():
        headers, types, rows = load_group_csv(group_file)
        try:
            log_date_col = headers.index("Log_Date")
        except ValueError:
            # Skip malformed group files with no Log_Date
            continue

        # Find the row for this date
        target_row = None
        for row in rows:
            if len(row) < len(headers):
                row.extend([""] * (len(headers) - len(row)))
            if row[log_date_col] == log_date:
                target_row = row
                break

        if target_row is None:
            continue  # no data for this date in this group

        # Collect only non-empty cells (including "N/A")
        non_empty = []
        for h, v in zip(headers, target_row):
            cell = v or ""
            if cell != "":
                non_empty.append((h, cell))

        if not non_empty:
            continue

        group_name = group_file.stem
        groups_with_data.append((group_name, non_empty))

    if not groups_with_data:
        msg = f"log-tool: No data for {log_date} in any group under {DATA_DIR}"
        log_event(msg)
        print(msg)
        return

    # Log a brief summary of the show operation
    log_event(f"SHOW date={log_date} groups={len(groups_with_data)}")

    print(f"log-tool: Logs for {log_date}\n")

    for group_name, non_empty in groups_with_data:
        key_width = max(len(h) for h, _ in non_empty)
        print(f"[Group: {group_name}]")
        for h, cell in non_empty:
            print(f"{h.ljust(key_width)} : {cell}")
        print()  # blank line between groups


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
                "  python3 log_tool.py history [N]"
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
            #   python3 log_tool.py show             -> show today's data
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

        else:
            msg = f"Unknown command: {command!r}. For now we support 'log', 'show', and 'history'."
            print(msg)
            log_event(f"ERROR {msg}")

    except Exception as e:
        # Catch anything unexpected so it also lands in log.txt
        err_msg = f"log-tool: ERROR {type(e).__name__}: {e}"
        log_event(err_msg)
        print(err_msg)


if __name__ == "__main__":
    main()
