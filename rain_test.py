import csv
import time
from collections import deque
from datetime import datetime, timedelta, timezone

import RPi.GPIO as GPIO

import sd_notify
from rain_common import (
    CSV_FIELDS,
    CSV_PATH,
    IN_PER_MM,
    LOG_DIR,
    MM_PER_TIP,
    RAIN_PIN,
    RATE_WINDOW_MINUTES,
    rate_mm_hr,
    read_rows,
)

REST_SECONDS = 0.75

GPIO.setmode(GPIO.BCM)
GPIO.setup(RAIN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def ensure_csv():
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    if not CSV_PATH.exists():
        with open(CSV_PATH, "w", newline="") as file:
            csv.writer(file).writerow(CSV_FIELDS)
        return

    # If a power cut left a half-written last line, end it so the next
    # entry starts on its own line (read_rows skips the broken one).
    with open(CSV_PATH, "rb+") as file:
        file.seek(0, 2)
        if file.tell() > 0:
            file.seek(-1, 2)
            if file.read(1) != b"\n":
                file.write(b"\n")


def log_tip(timestamp_utc, tip_count, rain_mm, rain_in, rate):
    with open(CSV_PATH, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            timestamp_utc,
            tip_count,
            f"{rain_mm:.4f}",
            f"{rain_in:.4f}",
            f"{rate:.2f}",
        ])


def load_previous_state():
    """Resume from the last good log row so totals survive a restart.

    Bad rows (e.g. half-written after a power cut) are skipped, so the
    count picks up from the last good row instead of falling back to 0.
    """
    rows = read_rows()
    if not rows:
        return 0, deque()

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=RATE_WINDOW_MINUTES)
    recent_tips = deque(r["time"] for r in rows if r["time"] >= cutoff)
    return rows[-1]["tip_count"], recent_tips


ensure_csv()
tip_count, recent_tips = load_previous_state()

print("Rain gauge logger started...")
print(f"Using GPIO{RAIN_PIN}; {MM_PER_TIP} mm per tip")
print(f"Logging to {CSV_PATH}")
print(f"Resuming at tip #{tip_count}")

sd_notify.ready()

try:
    while True:
        sd_notify.watchdog()

        if GPIO.input(RAIN_PIN) == 0:
            tip_count += 1
            now = datetime.now(timezone.utc)

            # Rate = rain in the last RATE_WINDOW_MINUTES, in mm/hr
            recent_tips.append(now)
            cutoff = now - timedelta(minutes=RATE_WINDOW_MINUTES)
            while recent_tips and recent_tips[0] < cutoff:
                recent_tips.popleft()

            rain_mm = tip_count * MM_PER_TIP
            rain_in = rain_mm * IN_PER_MM
            rate = rate_mm_hr(recent_tips, now)

            log_tip(now.isoformat(), tip_count, rain_mm, rain_in, rate)

            print(
                f"TIP #{tip_count} | "
                f"Rainfall: {rain_mm:.2f} mm / {rain_in:.3f} in | "
                f"Rate: {rate:.2f} mm/hr"
            )

            time.sleep(REST_SECONDS)

            while GPIO.input(RAIN_PIN) == 0:
                sd_notify.watchdog()
                time.sleep(0.01)

        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nStopping rain gauge logger.")
    GPIO.cleanup()
