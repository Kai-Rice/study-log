# groups.py
# CSV group handling, data-type validation, and core logging logic.

import csv
from pathlib import Path

from config import DATA_DIR, today_iso
from events import log_event


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


def validate_integer(value_str: str) -> int:
    """
    Validate that a string can be converted to an integer.
    Return the integer.
    """
    try:
        parsed_int = int(value_str)
    except ValueError:
        raise ValueError("Value must be an integer.")
    return parsed_int


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
