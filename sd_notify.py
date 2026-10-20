"""Minimal systemd notify client (no extra packages needed).

Lets a service tell systemd it is ready (READY=1) and still alive
(WATCHDOG=1). Outside systemd, NOTIFY_SOCKET is unset and calls do nothing.
"""
import os
import socket
import time


def notify(message):
    addr = os.environ.get("NOTIFY_SOCKET")
    if not addr:
        return

    # A leading "@" means an abstract socket
    if addr.startswith("@"):
        addr = "\0" + addr[1:]

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
            sock.connect(addr)
            sock.sendall(message.encode())
    except OSError:
        pass


def ready():
    notify("READY=1")


_last_ping = 0.0


def watchdog(min_interval=5):
    # Safe to call from tight loops; only pings every few seconds
    global _last_ping
    now = time.monotonic()
    if now - _last_ping >= min_interval:
        _last_ping = now
        notify("WATCHDOG=1")
