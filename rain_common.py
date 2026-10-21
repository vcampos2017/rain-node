"""Shared settings and helpers for the rain-node scripts.

rain_test.py (logger), rain_display.py (LCD) and api.py (web API) all
import from here, so they always agree on where the log lives and how
the numbers are calculated.
"""

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Paths are built from this file's own folder, so the scripts find the
# log no matter which folder they are started from (e.g. by systemd).
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
CSV_PATH = LOG_DIR / "rain_log.csv"

CSV_FIELDS = ["timestamp_utc", "tip_count", "rain_mm", "rain_in", "rate_mm_hr"]

# Hardware and calibration
RAIN_PIN = 18
MM_PER_TIP = 0.2794
IN_PER_MM = 0.0393701

# Rain rate = rain that fell in this many recent minutes, scaled to mm/hr.
RATE_WINDOW_MINUTES = 15


def read_rows():
    """Return all valid log rows as dicts with typed values.

    Rows that can't be parsed (for example a half-written line after a
    power cut) are skipped instead of crashing the caller.
    """
    rows = []
    try:
        with open(CSV_PATH, newline="") as f:
            for row in csv.DictReader(f):
                try:
                    rows.append({
                        "timestamp_utc": row["timestamp_utc"],
                        "time": datetime.fromisoformat(row["timestamp_utc"]),
                        "tip_count": int(row["tip_count"]),
                        "rain_mm": float(row["rain_mm"]),
                        "rain_in": float(row["rain_in"]),
                        "rate_mm_hr": float(row["rate_mm_hr"]),
                    })
                except (KeyError, TypeError, ValueError):
                    continue
    except FileNotFoundError:
        pass
    return rows


def rate_mm_hr(tip_times, now=None):
    """Current rain rate from the tips in the last RATE_WINDOW_MINUTES."""
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=RATE_WINDOW_MINUTES)
    recent = sum(1 for t in tip_times if t >= cutoff)
    return recent * MM_PER_TIP * (60 / RATE_WINDOW_MINUTES)
