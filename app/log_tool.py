# log-tool v0.2.0

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



def log_item(item_name: str, value_str: str, log_date: str | None = None) -> None:
   # Log an integer value for the given item_name on the given log_date.
    """
    - If log_date is None, use today's date.
    - Only supports Integer columns for now.
    """

    # 1) Decide which date to log to
    if log_date is None:
        log_date = today_iso()

    # 2) Load the CSV
    headers, types, rows = load_study_csv()

    # 3) Find relevant columns
    log_date_col = find_column(headers, "Log_Date")
    item_col     = find_column(headers, item_name)

    # 4) Ensure the column is Integer-typed
    item_type = types[item_col]
    if item_type != "Integer":
        raise RuntimeError(
            f"Column {item_name!r} has type {item_type!r}, "
            "but this alpha only supports Integer columns."
        )

    # 5) Validate and normalize the value
    value_int = validate_integer(value_str)
    value     = str(value_int)  # store as text in CSV

    # 6) Find or create the row for this log_date
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

    # 7) Read previous value for that cell (for the message)
    previous = target_row[item_col] or "N/A"

    # 8) Update the cell
    target_row[item_col] = value

    # 9) Save changes back to disk
    save_study_csv(headers, types, rows)

    # 10) Feedback
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
