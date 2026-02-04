# config.py
# Core configuration and version info for log-tool.

from pathlib import Path
from datetime import date

# Semantic version of the tool
APP_NAME = "study-log"
VERSION  = "0.9.0"

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR   = SCRIPT_DIR.parent
DATA_DIR   = ROOT_DIR / "data"
LOG_FILE   = SCRIPT_DIR / "log.txt"


def today_iso() -> str:
    """Return today's date as YYYY-MM-DD (ISO format)."""
    return date.today().isoformat()
