import time
from smbus import SMBus

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


import csv

LOG_FILE = "logs/rain_log.csv"

lcd_init()

def get_latest():
    try:
        with open(LOG_FILE) as f:
            lines = f.readlines()
            if len(lines) < 2:
                return None

            last = lines[-1].strip().split(",")

            rain_mm = float(last[2])
            rate = float(last[4])

            return rain_mm, rate
    except:
        return None


while True:
    line1 = "No data"
    line2 = "Waiting..."

    data = get_latest()

    if data:
        rain_mm, rate = data
        now = time.time()

        # Detect rain activity
        if rate > 0:
            SESSION_LAST_RAIN_TIME = now

            if not SESSION_ACTIVE:
                SESSION_ACTIVE = True
                SESSION_START_MM = rain_mm

        # Detect rain stop
        elif SESSION_ACTIVE and (now - SESSION_LAST_RAIN_TIME > SESSION_TIMEOUT):
            SESSION_ACTIVE = False

        if SESSION_ACTIVE:
            session_total = rain_mm - SESSION_START_MM
            line1 = f"Rain {rain_mm:.2f} mm"
            line2 = f"Sess {session_total:.2f} mm"
        else:
            line1 = f"Rain {rain_mm:.2f} mm"
            line2 = "No Rain"

    lcd_message(line1, LCD_LINE_1)
    lcd_message(line2, LCD_LINE_2)

    time.sleep(5)
