import csv
import os
import time
from datetime import datetime, timezone

import RPi.GPIO as GPIO

RAIN_PIN = 18

MM_PER_TIP = 0.2794
IN_PER_MM = 0.0393701
REST_SECONDS = 0.75

LOG_DIR = "logs"
CSV_PATH = os.path.join(LOG_DIR, "rain_log.csv")

GPIO.setmode(GPIO.BCM)
GPIO.setup(RAIN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

tip_count = 0
start_time = time.time()


def ensure_csv():
    os.makedirs(LOG_DIR, exist_ok=True)

    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                "timestamp_utc",
                "tip_count",
                "rain_mm",
                "rain_in",
                "rate_mm_hr",
            ])


def log_tip(timestamp_utc, tip_count, rain_mm, rain_in, rate_mm_hr):
    with open(CSV_PATH, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            timestamp_utc,
            tip_count,
            f"{rain_mm:.4f}",
            f"{rain_in:.4f}",
            f"{rate_mm_hr:.2f}",
        ])


ensure_csv()

print("Rain gauge test started...")
print(f"Using GPIO{RAIN_PIN}; {MM_PER_TIP} mm per tip")
print(f"Logging to {CSV_PATH}")

try:
    while True:
        if GPIO.input(RAIN_PIN) == 0:
            tip_count += 1

            rain_mm = tip_count * MM_PER_TIP
            rain_in = rain_mm * IN_PER_MM

            elapsed_hours = (time.time() - start_time) / 3600
            rate_mm_hr = rain_mm / elapsed_hours if elapsed_hours > 0 else 0

            timestamp_utc = datetime.now(timezone.utc).isoformat()

            log_tip(timestamp_utc, tip_count, rain_mm, rain_in, rate_mm_hr)

            print(
                f"TIP #{tip_count} | "
                f"Rainfall: {rain_mm:.2f} mm / {rain_in:.3f} in | "
                f"Rate: {rate_mm_hr:.2f} mm/hr"
            )

            time.sleep(REST_SECONDS)

            while GPIO.input(RAIN_PIN) == 0:
                time.sleep(0.01)

        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nStopping rain gauge test.")
    GPIO.cleanup()
