import RPi.GPIO as GPIO
import time

RAIN_PIN = 18

MM_PER_TIP = 0.2794
IN_PER_MM = 0.0393701
REST_SECONDS = 0.75

GPIO.setmode(GPIO.BCM)
GPIO.setup(RAIN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

tip_count = 0
start_time = time.time()

print("Rain gauge test started...")
print(f"Using GPIO{RAIN_PIN}; {MM_PER_TIP} mm per tip")

try:
    while True:
        if GPIO.input(RAIN_PIN) == 0:
            tip_count += 1

            rain_mm = tip_count * MM_PER_TIP
            rain_in = rain_mm * IN_PER_MM

            elapsed_hours = (time.time() - start_time) / 3600
            rate_mm_hr = rain_mm / elapsed_hours if elapsed_hours > 0 else 0

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
