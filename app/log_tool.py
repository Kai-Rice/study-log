# log-tool v0.3.0

from pathlib import Path
from datetime import date
import csv
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR   = SCRIPT_DIR.parent
DATA_DIR   = ROOT_DIR / "data"
STUDY_FILE = DATA_DIR / "study.csv" # STUDY_FILE points to ~log-tool/data/study.csv


def today_iso() -> str: # returns today's date as an ISO-formatted string (YYYY-MM-DD)
    return date.today().isoformat()


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



def log_item(item_name: str, value_str: str, log_date: str | None = None) -> None:
    """
    Log a value for the given item_name on the given log_date.

    Supported types:
      - integer  (SET behavior)
      - duration (ADD behavior, stored as hh:mm:ss)

    - If log_date is None, use today's date.
    """
    # 1) Decide which date to log to
    if log_date is None:
        log_date = today_iso()

    # 2) Load the CSV
    headers, types, rows = load_study_csv()

    # 3) Find relevant columns
    log_date_col = find_column(headers, "Log_Date")
    item_col     = find_column(headers, item_name)

    # 4) Look up the item type
    item_type = types[item_col]

    # 5) Find or create the row for this log_date
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

    #    # 6) Dispatch based on type
    if item_type == "integer":
        # integer behavior: SET
        value_int = validate_integer(value_str)
        value     = str(value_int)

        previous = target_row[item_col] or "N/A"
        target_row[item_col] = value

    elif item_type == "duration":
        # Duration behavior: ADD to existing
        added_seconds = parse_duration_to_seconds(value_str)

        existing_str = target_row[item_col].strip() if target_row[item_col] else ""
        if existing_str:
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

    else:
        raise RuntimeError(
            f"Column {item_name!r} has unsupported type {item_type!r} "
            "(supported: integer, duration)"
        )

    # 7) Save changes back to disk
    save_study_csv(headers, types, rows)

    # 8) Feedback
    print(f"log-tool: Updated {item_name} for {log_date}: (prev: {previous}) -> {value}")


def main() -> None:
    args = sys.argv[1:]

    # Basic command-line parsing
    if len(args) == 0:
        print("Usage: python3 log_tool.py log <ItemName> <Value> [-YYYY-MM-DD]")
        return

    command = args[0]

    if command == "log":
        if len(args) not in (3, 4):
            print("Usage: python3 log_tool.py log <ItemName> <Value> [-YYYY-MM-DD]")
            return

        _, item_name, value_str = args[0:3]
        log_date = None

        if len(args) == 4:
            date_flag = args[3]  # expects something like -2026-02-01
            if not date_flag.startswith("-"):
                print("Date flag must start with '-' and use YYYY-MM-DD, e.g. -2026-02-01")
                return
            log_date = date_flag[1:]  # strip the leading '-'
            # (Optional) validate format here with datetime.date.fromisoformat

        log_item(item_name, value_str, log_date=log_date)

    else:
        print(f"Unknown command: {command!r}. For now we only support 'log'.")



if __name__ == "__main__":
    main()
