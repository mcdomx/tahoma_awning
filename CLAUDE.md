# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A FastAPI service for controlling a Somfy TaHoma awning locally via the `pyoverkiz` library. Runs in Docker and exposes HTTP endpoints for each awning command. Connects directly to the local TaHoma gateway over HTTPS rather than through Somfy's cloud.

## Environment

```bash
docker compose build    # build the image
docker compose up       # start the service (port 8765 by default)
```

Dependencies: `pyoverkiz`, `aiohttp`, `python-dotenv`, `fastapi`, `uvicorn` (Python 3.9)

## Architecture

```
app/
  client.py     # make_client() factory — builds OverkizClient targeting the local gateway
  commands.py   # async control functions (deploy, undeploy, stop, my_position, get_devices)
  api.py        # FastAPI app and route definitions
main.py         # uvicorn entry point (port 8765)
Dockerfile
docker-compose.yml
```

**Connection pattern**: `make_client()` in `app/client.py` builds an `OverkizClient` targeting the local gateway at `https://{TAHOMA_HOST}:8443/enduser-mobile-web/1/enduserAPI/`. Each control function opens a fresh `async with make_client()` context, logs in, sends one command, then closes — no persistent session. SSL verification is disabled because the local gateway uses a self-signed certificate.

**Device**: `rts://1611-2003-9170/16775800` — an RTS horizontal awning (`rts:HorizontalAwningRTSComponent`)

**Available commands** (from device definition): `deploy`, `undeploy`, `open`, `close`, `up`, `down`, `stop`, `my`, `test`, `rest`, `identify`, `openConfiguration`
- `deploy` / `down` are equivalent; `undeploy` / `up` are equivalent

## API Endpoints

| Method | Path | Action |
|--------|------|--------|
| GET | `/health` | Service health check |
| GET | `/awning/deploy` | Extend the awning fully |
| GET | `/awning/undeploy` | Retract the awning fully |
| GET | `/awning/stop` | Stop movement immediately |
| GET | `/awning/my` | Move to preset "my" position |
| GET | `/awning/devices` | List all devices on the gateway |

## Credentials (.env)

```
TAHOMA_USER    # Somfy account username
TAHOMA_PW      # Somfy account password
TAHOMA_PIN     # TaHoma gateway PIN (kept for reference)
TAHOMA_KEY     # Local API token
TAHOMA_HOST    # Gateway IP address (e.g. 192.168.1.x) — used instead of mDNS
AWNING_PORT    # Host port exposed by docker-compose (default: 8765)
CICD_DEPLOY_MODE       # docker (this project runs entirely in Docker)
CICD_GIT_BRANCH        # branch the Pi polls for new commits (default: main)
CICD_INTERVAL_MINUTES  # minimum minutes between deploy attempts (default: 15)
```

## CI/CD (Pi auto-deploy)

`scripts/cicd_update.py`, run every minute via cron on the Pi, polls `origin/<CICD_GIT_BRANCH>` and on new commits runs `git pull` + `docker compose pull && up -d`. See `README-PI.md` for full Pi setup, cron entry, and pause/resume (`touch .cicd_disabled`).
