#!/bin/bash
# Install rain-node systemd services with auto-restart and watchdogs.
# Usage: sudo ./install.sh
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "Run with sudo: sudo ./install.sh"
    exit 1
fi

DIR="$(cd "$(dirname "$0")" && pwd)"
RUN_USER="${SUDO_USER:-pi}"
UNITS="rain-sensor rain-display rain-api"

mkdir -p "$DIR/logs"
chown "$RUN_USER": "$DIR/logs"

# The old single service would run a second copy alongside the new ones
if [ -f /etc/systemd/system/rain-node.service ]; then
    echo "Disabling old rain-node.service (replaced by $UNITS)"
    systemctl disable --now rain-node.service || true
fi

for unit in $UNITS; do
    sed -e "s|@USER@|$RUN_USER|g" -e "s|@DIR@|$DIR|g" \
        "$DIR/systemd/$unit.service" > "/etc/systemd/system/$unit.service"
done

cp "$DIR/systemd/wifi-powersave-off.service" /etc/systemd/system/

mkdir -p /etc/systemd/system.conf.d
cp "$DIR/systemd/watchdog.conf" /etc/systemd/system.conf.d/watchdog.conf

systemctl daemon-reload
systemctl daemon-reexec  # picks up the hardware watchdog setting
systemctl enable --now wifi-powersave-off.service || echo "No wlan0, skipping Wi-Fi power-save fix"

for unit in $UNITS; do
    systemctl enable --now "$unit.service"
done

echo
systemctl --no-pager --lines=0 status $UNITS
