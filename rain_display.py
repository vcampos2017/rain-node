import socket
import time
from smbus import SMBus

import sd_notify
from rain_common import CSV_PATH, read_rows

SESSION_ACTIVE = False
SESSION_START_MM = 0
SESSION_LAST_RAIN_TIME = 0
SESSION_TIMEOUT = 300  # 5 minutes

I2C_ADDR = 0x27
LCD_WIDTH = 16

LCD_CHR = 1
LCD_CMD = 0

LCD_LINE_1 = 0x80
LCD_LINE_2 = 0xC0

ENABLE = 0b00000100
BACKLIGHT = 0b00001000

SCREEN_SECONDS = 5
BOOT_IP_SECONDS = 10
IP_EVERY_N_SCREENS = 3  # show hostname/IP every 3rd screen


bus = SMBus(1)


def lcd_toggle_enable(bits):
    time.sleep(0.0005)
    bus.write_byte(I2C_ADDR, bits | ENABLE)
    time.sleep(0.0005)
    bus.write_byte(I2C_ADDR, bits & ~ENABLE)
    time.sleep(0.0005)


def lcd_byte(bits, mode):
    high = mode | (bits & 0xF0) | BACKLIGHT
    low = mode | ((bits << 4) & 0xF0) | BACKLIGHT

    bus.write_byte(I2C_ADDR, high)
    lcd_toggle_enable(high)

    bus.write_byte(I2C_ADDR, low)
    lcd_toggle_enable(low)


def lcd_init():
    lcd_byte(0x33, LCD_CMD)
    lcd_byte(0x32, LCD_CMD)
    lcd_byte(0x06, LCD_CMD)
    lcd_byte(0x0C, LCD_CMD)
    lcd_byte(0x28, LCD_CMD)
    lcd_byte(0x01, LCD_CMD)
    time.sleep(0.005)


def lcd_message(message, line):
    message = message.ljust(LCD_WIDTH)
    lcd_byte(line, LCD_CMD)

    for char in message[:LCD_WIDTH]:
        lcd_byte(ord(char), LCD_CHR)


def lcd_show(line1, line2):
    # A loose wire or I2C noise raises OSError; re-init and retry once
    # instead of letting the whole display service die.
    for attempt in range(2):
        try:
            lcd_message(line1, LCD_LINE_1)
            lcd_message(line2, LCD_LINE_2)
            return
        except OSError as e:
            print(f"LCD write failed ({e}), re-initialising")
            time.sleep(0.5)
            try:
                lcd_init()
            except OSError:
                pass


def get_ip():
    # Connecting a UDP socket sends nothing; it just makes the OS pick
    # the interface/address used for the default route.
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "No network"


def network_screen():
    return socket.gethostname()[:LCD_WIDTH], get_ip()


def get_latest():
    # read_rows skips damaged lines, so one bad row can't blank the screen
    try:
        rows = read_rows()
    except OSError as e:
        print(f"Could not read {CSV_PATH}: {e}")
        return None

    if not rows:
        return None

    last = rows[-1]
    return last["tip_count"], last["rain_mm"], last["rate_mm_hr"]


try:
    lcd_init()
except OSError as e:
    print(f"LCD init failed ({e}), will retry on first write")

sd_notify.ready()

# Show the address right away so it's easy to SSH in after boot
host, ip = network_screen()
lcd_show(host, ip)
sd_notify.watchdog(min_interval=0)
time.sleep(BOOT_IP_SECONDS)

LAST_TIP_COUNT = None
screen = 0

while True:
    sd_notify.watchdog(min_interval=0)

    line1 = "No data"
    line2 = "Waiting..."

    data = get_latest()

    if data:
        tip_count, rain_mm, rate = data
        now = time.time()

        # First run, or the log was reset, initializes the baseline
        # without starting a session
        if LAST_TIP_COUNT is None or tip_count < LAST_TIP_COUNT:
            LAST_TIP_COUNT = tip_count

        # A new bucket tip means rain activity
        elif tip_count > LAST_TIP_COUNT:
            SESSION_LAST_RAIN_TIME = now

            if not SESSION_ACTIVE:
                SESSION_ACTIVE = True
                SESSION_START_MM = rain_mm

            LAST_TIP_COUNT = tip_count

        # End the session after no new tips for the timeout period
        elif SESSION_ACTIVE and (now - SESSION_LAST_RAIN_TIME > SESSION_TIMEOUT):
            SESSION_ACTIVE = False

        if SESSION_ACTIVE:
            session_total = rain_mm - SESSION_START_MM
            line1 = f"Rain {rain_mm:.2f} mm"
            line2 = f"Sess {session_total:.2f} mm"
        else:
            line1 = f"Rain {rain_mm:.2f} mm"
            line2 = "No Rain"

    screen += 1
    if screen % IP_EVERY_N_SCREENS == 0:
        line1, line2 = network_screen()

    lcd_show(line1, line2)

    time.sleep(SCREEN_SECONDS)
