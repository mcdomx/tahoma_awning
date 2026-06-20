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
```

---

## 6. Install Dependencies and Start the Service

```bash
docker compose up -d --build
```

This builds the image and starts the `tahoma-service` container with `restart: unless-stopped`, so it comes back up automatically after a reboot or crash.

---

## 7. Set Up CI/CD (Auto-Deploy on New Commits)

Add a cron entry that polls `origin/main` every minute and redeploys when new commits land:

```bash
crontab -e
```

Add this line:

```
* * * * * ENVIRONMENT=production /usr/bin/python3 /home/mcdomx/tahoma_awning/scripts/cicd_update.py
```

This fires every minute but gates on `CICD_INTERVAL_MINUTES` (default: 15). Logs go to `logs/cicd.log`.

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

## 8. Verify

```bash
docker compose ps
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
