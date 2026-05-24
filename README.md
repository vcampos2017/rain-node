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
## systemd Service (Auto Start)

The rain-node runs as a background service using systemd.

Service file location:
/etc/systemd/system/rain-node.service
