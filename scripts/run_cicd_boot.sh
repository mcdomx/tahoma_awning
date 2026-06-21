#!/usr/bin/env bash
# Run once at boot (via @reboot cron) to catch up on any commits that landed
# while the Pi was off. Bypasses CICD_INTERVAL_MINUTES; still only rebuilds
# if origin/<branch> is ahead of HEAD. Waits for Docker to be ready first,
# since @reboot can fire before dockerd has finished starting.
set -u

for _ in $(seq 1 30); do
    /usr/bin/docker info >/dev/null 2>&1 && break
    sleep 2
done

ENVIRONMENT=production /usr/bin/python3 "$(dirname "$0")/cicd_update.py" --ignore-interval
