# Raspberry Pi Setup — tahoma_awning

## 1. Flash the SD Card

### Install Raspberry Pi Imager

Download from **raspberrypi.com/software** (Mac, Windows, Linux).

### Flash

1. Insert your SD card (32GB+ recommended, Class 10 / A1 or faster)
2. Open Raspberry Pi Imager
3. **Choose Device** → your Pi model (e.g. Raspberry Pi 4)
4. **Choose OS** → Raspberry Pi OS Lite (64-bit)
5. **Choose Storage** → your SD card
6. Click **Next**, then **Edit Settings** when prompted

### Customize before flashing

**General tab:**
- Hostname: `tahomaawning` (or your preference)
- Username: `mcdomx`
- Password: set a strong password
- WiFi SSID and password

**Services tab:**
- Enable SSH → Use password authentication

Click **Save** → **Yes** → **Yes** to flash.

---

## 2. First Boot

Insert the SD card, power on the Pi, wait ~60 seconds, then SSH in:

```bash
ssh mcdomx@tahomaawning.local
```

If `.local` doesn't resolve, find the Pi's IP from your router and use that instead.

---

## 3. System Prerequisites

```bash
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
rm get-docker.sh

# Add your user to the docker group (avoids needing sudo for docker commands)
sudo usermod -aG docker $USER
# Log out and back in (or `newgrp docker`) for the group change to take effect

# Verify Docker Compose plugin is available
docker compose version
```

---

## 4. Clone the Repo

```bash
cd ~
git clone https://github.com/mcdomx/tahoma_awning.git tahoma_awning
cd tahoma_awning
```

---

## 5. Configure Environment

```bash
nano .env
```

See `CLAUDE.md` (or `README.md`) for the full list of supported env vars. At minimum, this project needs its normal runtime config (`TAHOMA_USER`, `TAHOMA_PW`, `TAHOMA_PIN`, `TAHOMA_KEY`, `TAHOMA_HOST`, `AWNING_PORT`) plus the CI/CD variables below:

```
CICD_DEPLOY_MODE=docker
CICD_GIT_BRANCH=main
CICD_INTERVAL_MINUTES=15
CICD_COMPOSE_FILE=docker-compose.pi.yml
```

---

## 6. Enable I2C for the LCD Display (optional)

Skip this step if you aren't wiring up the status LCD. See `README-LCD.md` for
wiring and the full feature description.

```bash
sudo raspi-config        # Interface Options -> I2C -> Enable
sudo reboot
```

(Equivalent: ensure `dtparam=i2c_arm=on` in `/boot/firmware/config.txt`.)

After reboot, install `i2c-tools` and confirm the LCD is detected:

```bash
sudo apt install -y i2c-tools
i2cdetect -y 1
```

You should see the device at `27` (the default) or `3f`. If it shows `3f`, set
`LCD_I2C_ADDRESS=0x3f` in `.env`.

---

## 7. Install Dependencies and Start the Service

```bash
docker compose -f docker-compose.pi.yml up -d --build
```

`docker-compose.pi.yml` is the same service as `docker-compose.yml` plus
`/dev/i2c-1` device passthrough for the LCD. If you skipped step 6, this still
works — the app detects the missing display and runs without it. This starts
the `tahoma-service` container with `restart: unless-stopped`, so it comes
back up automatically after a reboot or crash.

---

## 8. Set Up CI/CD (Auto-Deploy on New Commits)

Add a cron entry that polls `origin/main` every minute and redeploys when new commits land:

```bash
crontab -e
```

Add these lines:

```
* * * * * ENVIRONMENT=production /usr/bin/python3 /home/mcdomx/tahoma_awning/scripts/cicd_update.py
@reboot /home/mcdomx/tahoma_awning/scripts/run_cicd_boot.sh
```

The first line fires every minute but gates on `CICD_INTERVAL_MINUTES` (default: 15) and rebuilds the container (`docker compose up -d --build`) whenever new commits are found — `up -d` alone wouldn't pick up code changes since the image is built locally, not pulled from a registry.

The `@reboot` line runs once after a reboot (waiting for Docker to be ready first), bypassing the interval throttle so any commits that landed while the Pi was off are picked up and rebuilt immediately, rather than waiting up to `CICD_INTERVAL_MINUTES`. It still only rebuilds if `origin/<branch>` is ahead of `HEAD`.

Logs go to `logs/cicd.log`.

**Pause / resume without editing cron:**

```bash
touch .cicd_disabled   # pause
rm .cicd_disabled      # resume
```

**Manual trigger:**

```bash
./scripts/run_cicd.sh
```

---

## 9. Verify

```bash
docker compose -f docker-compose.pi.yml ps
curl http://localhost:8765/health
tail -f logs/cicd.log
```

Confirm `mcdomx` is in the `docker` group (required for `docker compose` to work from the cron job without `sudo`):

```bash
groups $USER | grep docker
```

---

## Troubleshooting

**pipenv not found in CI/CD** — Check `which pipenv` on the Pi. If cron can't find it, add a `PATH=` line to the crontab (cron doesn't source `~/.bashrc`), e.g.:
```
PATH=/home/mcdomx/.local/bin:/usr/local/bin:/usr/bin:/bin
```

**docker: permission denied** — Usually means the user wasn't added to the `docker` group, or the group change hasn't taken effect in the current shell. Log out/in (or reboot) and retry `docker compose ps`.

**No new commits detected** — `scripts/cicd_update.py` compares `HEAD` against `origin/<branch>` via `git fetch`. If the Pi's clone is on a different branch than `CICD_GIT_BRANCH`, it will never see updates. Check with `git branch --show-current`.

**LCD powered on but blank** — `i2cdetect` not found usually means step 6 was skipped; run `sudo apt install -y i2c-tools` and retry `i2cdetect -y 1`. If the device shows up but the screen is still blank, it's almost always the contrast potentiometer on the backpack — turn it with a small screwdriver while powered on. See `README-LCD.md` for the full LCD troubleshooting list.
