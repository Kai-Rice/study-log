# 📚 Study-Log

> Study-Log is a small, terminal-based logging tool for tracking daily metrics (study time, mood, habits, etc.) in **plain CSV files**. All data stays local, human-editable, and scriptable.

---

## Features (current)

- **CLI entrypoint**

  Run the tool with:

```bash
  python3 app/log_tool.py ...
```


## Project structure
```
study-log/
├─ app/
│  ├─ log_tool.py   # CLI entrypoint
│  ├─ config.py     # paths, version, shared configuration
│  ├─ events.py     # event logging (log.txt), history
│  └─ groups.py     # CSV loading/saving, type handling, log/search logic
├─ data/
│  ├─ study.csv     # example "study" group
│  └─ mood.csv      # example "mood" group
└─ README.md
```

---

## Installation

Requirements:

* Python 3.10+ (3.11+ recommended)

Clone the repository:

```bash
git clone <url>
cd study-log
```

(Optional) set up a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Make sure you have a `data/` directory with at least one CSV (for example `study.csv` and `mood.csv` as above).

---

## Usage

From the repo root:

```bash
python3 app/log_tool.py <command> [...]
```
