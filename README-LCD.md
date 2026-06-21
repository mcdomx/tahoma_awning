# LCD Status Display (I2C 1602) — Setup Guide

This project can drive a **Hosyond I2C IIC 1602 LCD (16x2, PCF8574 backpack)**
attached to the Raspberry Pi to show the awning's status at a glance — no
browser or HTTP client needed.

The display is **completely optional**. If the LCD is unplugged, the library is
missing, or the I2C bus errors, the application keeps running and serving the
API normally. You can wire it up at any time.

## What it shows

A fixed 16x2 layout, refreshing every second:

```
STATUS: DEPLOYED     <- last known position: DEPLOYED / RETRACTED / STOPPED / UNKNOWN
DEPLOYING 12S        <- current action: IDLE, DEPLOYING <n>S, or RETRACTING <n>S
```

The RTS awning motor has **no position feedback** — there's no sensor telling
the gateway (or this service) where the awning physically is. So both lines
are tracked optimistically from the commands this service has sent, not read
from hardware:

- **Status** (line 1) is set when an action completes: a full `deploy` →
  `DEPLOYED`, a full `undeploy` → `RETRACTED`, any `stop`/`my`/timed move →
  `STOPPED`. Before any command has been sent this boot, it reads `UNKNOWN`.
- **Action** (line 2) shows `IDLE` when nothing is moving. For a timed
  `/awning/deploy/timed` or `/awning/undeploy/timed` call, the countdown
  counts down the requested seconds. For a full (non-timed) `/awning/deploy`
  or `/awning/undeploy` call — where the motor runs until it hits its
  end-of-travel limit switch — the countdown instead counts down
  `AWNING_TRAVEL_SECONDS`, an estimate of how long a full traverse takes, then
  automatically reverts to `IDLE` and updates the status line. If you send a
  `stop` before that estimate elapses, the display updates immediately and the
  stale countdown is discarded.

## 1. Wiring

The module has a 4-pin I2C backpack. Connect it to the Pi 40-pin header:

| LCD pin | Pi pin            | Pi signal      |
|---------|-------------------|----------------|
| VCC     | Pin 2 (or 4)      | 5V             |
| GND     | Pin 6             | GND            |
| SDA     | Pin 3             | GPIO2 / SDA1   |
| SCL     | Pin 5             | GPIO3 / SCL1   |

> The 1602 needs **5V** on VCC for a usable backlight/contrast. SDA/SCL are 3.3V
> logic from the Pi; the PCF8574 backpack tolerates this fine.

```
 Pi header (top-left corner)
  1  2 (5V)  --> VCC
  3 (SDA) ----> SDA
  5 (SCL) ----> SCL
  6 (GND) ----> GND
```

## 2. Enable I2C on the Pi

```bash
sudo raspi-config        # Interface Options -> I2C -> Enable
sudo reboot
```

(Equivalent: ensure `dtparam=i2c_arm=on` in `/boot/firmware/config.txt`.)

## 3. Find the I2C address

```bash
sudo apt install -y i2c-tools
i2cdetect -y 1
```

You should see the device at `27` (the default) or `3f`. If it shows `3f`, set
`LCD_I2C_ADDRESS=0x3f` in `.env`.

## 4. Run via the Pi-specific compose file

This service runs in Docker (`CICD_DEPLOY_MODE=docker`), so the container needs
the I2C device node passed through from the host. The base `docker-compose.yml`
(used for local/dev builds where no `/dev/i2c-1` exists) does **not** include
this; `docker-compose.pi.yml` does:

```bash
docker compose -f docker-compose.pi.yml up -d --build
```

The CI/CD script already points at this file via `CICD_COMPOSE_FILE` in
`.env` (see below), so auto-deploys on the Pi pick it up automatically. The
container runs as root, so no host `i2c` group membership is required for the
container itself to open `/dev/i2c-1`.

## 5. Dependencies

The LCD libraries (`RPLCD`, `smbus2`) are declared in the `Pipfile` with a
`sys_platform == 'linux'` marker, so they install automatically on the Pi (and
inside the Linux container) and are skipped on macOS dev machines.

## 6. Configuration (`.env`)

| Variable                | Default                  | Purpose                                                        |
|--------------------------|---------------------------|------------------------------------------------------------------|
| `LCD_ENABLED`            | `auto`                    | `auto` (use LCD if present), `true`, or `false`                  |
| `LCD_I2C_ADDRESS`        | `0x27`                    | I2C address from `i2cdetect` (`0x27` or `0x3f`)                  |
| `LCD_I2C_PORT`           | `1`                       | I2C bus number (`1` on all modern Pis)                           |
| `LCD_UPDATE_SECONDS`     | `1`                       | Display refresh interval (kept low so countdowns look live)      |
| `AWNING_TRAVEL_SECONDS`  | `25`                      | Estimated full deploy/undeploy travel time (tune to your awning) |
| `CICD_COMPOSE_FILE`      | `docker-compose.pi.yml`   | Compose file the CI/CD script deploys with on the Pi             |

In `auto` mode (the default), the app enables the display only if the library
imports and the LCD initializes; otherwise it logs a line and runs without it.
Set `LCD_ENABLED=false` to force it off even when an LCD is attached.

## Troubleshooting

- **Blank / dim screen with a lit backlight** — adjust the small blue
  potentiometer on the backpack to set contrast.
- **`i2cdetect` shows nothing** — re-check wiring (SDA/SCL not swapped), confirm
  I2C is enabled and the Pi was rebooted.
- **Wrong characters / garbled text** — usually a contrast issue or the wrong
  address; verify `LCD_I2C_ADDRESS` matches `i2cdetect`.
- **Container can't open `/dev/i2c-1`** — confirm you deployed with
  `docker-compose.pi.yml` (not the plain `docker-compose.yml`), and that
  `/dev/i2c-1` exists on the host (`ls /dev/i2c-1`).
- **Status/action never change from `UNKNOWN`/`IDLE`** — the LCD only reflects
  commands sent through this service; it has no way to see manual remote
  control of the awning.
- **Confirm graceful operation** — unplug the LCD and restart the service; the
  API continues to work and the logs note the display was not detected.
