# study-log v0.1.0

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



# def log_item(item_name: str, value_str: str) -> None:
#     print(f"[log_item] would log: {item_name} = {value_str}")

def log_item(item_name: str, value_str: str) -> None:
    """
    Temporary debug version:
    - Load study.csv
    - Show headers and types
    - Show what we plan to log
    """
    headers, types, rows = load_study_csv()

    print("[log_item] Loaded study.csv")
    print("  STUDY_FILE:", STUDY_FILE)
    print("  Headers:", headers)
    print("  Types:", types)
    print(f"  Would log: {item_name} = {value_str}")



def main() -> None: # parsing + routing

    args = sys.argv[1:] # skip script name

    if len(args) == 0: # if no arguments are provided
        print("Usage: python log_tool.py log <ItemName> <Value>")
        return
   
    command = args[0] # first argument is the command

    if command == "log": # checks if the command is "log"
        if len(args) != 3: # expects exactly 3 arguments for "log" command
            print("Usage: python log_tool.py log <ItemName> <Value>")
            return
        
        # unpacks the args list into variables
        _, item_name, value_str = args
        print(f"[main] command={command}, item_name={item_name}, value={value_str}")

        # Call the core logic function
        log_item(item_name, value_str)

    else: # unknown command
        print(f"Unknown command: {command!r}. For now we only support 'log'.")


if __name__ == "__main__":
    main()
