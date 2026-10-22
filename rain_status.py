"""Print a short rain-node status summary in the terminal.

Meant to run when you log in over SSH (see README), but you can also run
it any time with: python3 rain_status.py
"""
import socket
import subprocess
import sys
from datetime import datetime, timedelta, timezone

from rain_common import IN_PER_MM, MM_PER_TIP, RATE_WINDOW_MINUTES, rate_mm_hr, read_rows

SERVICES = ["rain-sensor", "rain-display", "rain-api"]

COLOR = sys.stdout.isatty()


def paint(text, code):
    return f"\033[{code}m{text}\033[0m" if COLOR else text


def get_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "no network"


def service_state(name):
    try:
        result = subprocess.run(
            ["systemctl", "is-active", name],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip() or "unknown"
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"


def amount(mm):
    return f"{mm:6.2f} mm  ({mm * IN_PER_MM:.3f} in)"


def ago(delta):
    minutes = int(delta.total_seconds() // 60)
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{minutes} min ago"
    hours, minutes = divmod(minutes, 60)
    if hours < 48:
        return f"{hours} h {minutes} min ago"
    return f"{hours // 24} days ago"


def main():
    rows = read_rows()
    now = datetime.now(timezone.utc)
    midnight = datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    times = [r["time"] for r in rows]

    title = f" RAIN-NODE  {socket.gethostname()} @ {get_ip()} "
    print(paint(title, "30;42"))

    if rows:
        last = rows[-1]
        today_mm = sum(1 for t in times if t >= midnight) * MM_PER_TIP
        day_mm = sum(1 for t in times if t >= now - timedelta(hours=24)) * MM_PER_TIP
        local_last = last["time"].astimezone()

        print(f"  Total:     {amount(last['rain_mm'])}   {last['tip_count']} tips")
        print(f"  Today:     {amount(today_mm)}")
        print(f"  Last 24 h: {amount(day_mm)}")
        print(f"  Rate:      {rate_mm_hr(times, now):6.2f} mm/hr (last {RATE_WINDOW_MINUTES} min)")
        print(f"  Last tip:  {ago(now - last['time'])} ({local_last:%a %H:%M})")
    else:
        print("  No rain logged yet.")

    states = []
    for name in SERVICES:
        state = service_state(name)
        dot = paint("●", "32" if state == "active" else "31")
        states.append(f"{dot} {name.removeprefix('rain-')} {state}")
    print("  Services:  " + "   ".join(states))


if __name__ == "__main__":
    main()
