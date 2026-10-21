# rain-node

Raspberry Pi rain gauge node using a tipping bucket rain sensor.

## Hardware

- Raspberry Pi Zero 2 W
- Tipping bucket rain gauge / reed switch
- GPIO18 for rain gauge signal
- 10k pull-up resistor
- 0.047 uF capacitor for debounce/noise filtering

## Calibration

- 1 bucket tip = 0.2794 mm
- 1 mm = 0.0393701 inches

## Current script

`rain_test.py` counts bucket tips and prints tip count, rainfall, and estimated rain rate.

## Run

```bash
python3 rain_test.py
```
## LCD display

`rain_display.py` shows rain totals on a 16x2 I2C LCD (address 0x27). It shows
the hostname and IP address for 10 seconds at boot, then every 3rd screen, so
you can find the node on the network without a monitor.

## Services, auto-restart and crash recovery

Install everything as systemd services:

```bash
sudo ./install.sh
```

This installs and starts three services, running as the user who ran `sudo`:

| Service | Runs |
|---|---|
| `rain-sensor` | `rain_test.py` (counts tips, writes `logs/rain_log.csv`) |
| `rain-display` | `rain_display.py` (LCD) |
| `rain-api` | `api.py` (HTTP `/status` on port 5000) |

Recovery layers:

- **Crash:** every service has `Restart=always`, so systemd restarts it 5 s after it exits.
- **Hang:** the sensor and display loops ping the systemd watchdog. If a loop
  stops pinging for 60 s (for example a stuck I2C write), systemd kills and restarts it.
- **System freeze:** the Pi hardware watchdog is enabled
  (`/etc/systemd/system.conf.d/watchdog.conf`) and reboots the Pi if the OS stops responding for 15 s.
- **Wi-Fi dropouts:** Wi-Fi power saving is turned off (`wifi-powersave-off.service`).
- **Restarts keep totals:** `rain_test.py` resumes the tip count from the last row of the log.

If an older `/etc/systemd/system/rain-node.service` exists, the installer
disables it so two copies don't run at once.

Useful commands:

```bash
systemctl status rain-sensor rain-display rain-api
journalctl -u rain-display -f
sudo systemctl restart rain-display
```
