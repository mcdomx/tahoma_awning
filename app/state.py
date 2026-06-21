"""In-memory awning status tracker.

The RTS device has no position feedback, so "status" and "action" are
tracked optimistically from the commands this service has sent, not from
the hardware. Used by app/display.py to render the LCD.
"""

import threading
import time
from typing import Optional

_lock = threading.Lock()
_position: str = "UNKNOWN"  # DEPLOYED, RETRACTED, STOPPED, UNKNOWN
_action: str = "IDLE"  # IDLE, DEPLOYING, RETRACTING
_action_started_at: Optional[float] = None
_action_total_seconds: Optional[float] = None  # None when duration is unknown
_epoch: int = 0  # bumped on every start_action; lets stale auto-settles no-op


def start_action(action: str, total_seconds: Optional[float] = None) -> int:
    """Begin tracking an action. Returns an epoch token for end_action()."""
    global _action, _action_started_at, _action_total_seconds, _epoch
    with _lock:
        _action = action
        _action_started_at = time.monotonic()
        _action_total_seconds = total_seconds
        _epoch += 1
        return _epoch


def end_action(position: str, epoch: Optional[int] = None) -> None:
    """Mark the action finished. If epoch is given and stale, this is a no-op."""
    global _action, _action_started_at, _action_total_seconds, _position, _epoch
    with _lock:
        if epoch is not None and epoch != _epoch:
            return
        _action = "IDLE"
        _action_started_at = None
        _action_total_seconds = None
        _position = position


def get_status() -> dict:
    """Return current position/action, resolving any timed countdown live."""
    with _lock:
        action, started_at, total = _action, _action_started_at, _action_total_seconds
        position = _position

    if action == "IDLE" or started_at is None:
        return {"position": position, "action": "IDLE", "remaining_seconds": None}

    elapsed = time.monotonic() - started_at
    remaining = max(0, round(total - elapsed)) if total is not None else None
    return {"position": position, "action": action, "remaining_seconds": remaining}
