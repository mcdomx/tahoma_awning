# Tahoma Awning Control

Control a Somfy TaHoma awning directly from your local network — no cloud required. Runs as a Docker service with a REST API, built on [`pyoverkiz`](https://github.com/iMicknl/python-overkiz-api).

## Requirements

- Docker and Docker Compose
- A Somfy TaHoma gateway on your local network
- Your Somfy account credentials, gateway PIN, and local API token

## Setup

**1. Configure credentials**

Edit `.env` in the project root:

```
TAHOMA_USER=your_somfy_email
TAHOMA_PW=your_somfy_password
TAHOMA_PIN=1234-5678-9012       # printed on the back of your TaHoma box
TAHOMA_KEY=your_local_api_token # obtained from the TaHoma local API
TAHOMA_HOST=192.168.x.x         # local IP address of your TaHoma gateway
AWNING_PORT=8765                # host port to expose (default: 8765)
```

`TAHOMA_HOST` must be the gateway's IP address (not the `.local` hostname) so the Docker container can reach it.

**2. Build and start**

```bash
docker compose up --build
```

**3. Verify**

```bash
curl http://localhost:8765/health
# {"status":"ok"}
```

## API

All endpoints use `GET` and return `{"status": "ok"}` on success or a `500` with an error detail on failure.

| Endpoint | Action |
|---|---|
| `GET /health` | Service health check |
| `GET /awning/deploy` | Extend the awning fully |
| `GET /awning/undeploy` | Retract the awning fully |
| `GET /awning/stop` | Stop movement immediately |
| `GET /awning/my` | Move to the preset "my" position |
| `GET /awning/devices` | List all devices registered to the gateway |

Example:

```bash
curl http://localhost:8765/awning/deploy
curl http://localhost:8765/awning/stop
curl http://localhost:8765/awning/undeploy
```

## How It Works

Each API call opens a fresh HTTPS connection to the TaHoma gateway at `https://{TAHOMA_HOST}:8443`, authenticates with the local API token, sends a single RTS command to the awning device, then closes the connection. No persistent session is maintained.

The awning communicates over the RTS radio protocol (`rts:HorizontalAwningRTSComponent`). Because RTS is one-way radio, the gateway cannot read the awning's current position — only issue commands.

## Port Configuration

The service listens on port `8765` inside the container. To expose it on a different host port, set `AWNING_PORT` in `.env`:

```
AWNING_PORT=9000
```
