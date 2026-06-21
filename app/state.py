"""In-memory awning status tracker.

The RTS device has no position feedback, so "last movement" and "action" are
tracked optimistically from the commands this service has sent, not from
the hardware. Used by app/display.py to render the LCD.
"""

import threading
import time
from typing import Optional

_lock = threading.Lock()
_last_movement: str = "INITIAL STATE"  # e.g. "FULLY DEPLOYED", "DEPLOYED 2s"; stop is not a movement
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


def end_action(movement: Optional[str] = None, epoch: Optional[int] = None) -> None:
    """Mark the action finished. If epoch is given and stale, this is a no-op.

    `movement` records what just happened (e.g. "FULLY DEPLOYED") for line 1 of
    the LCD. Pass None for non-movement stops (e.g. an explicit /awning/stop)
    so the last recorded movement stays on screen.
    """
    global _action, _action_started_at, _action_total_seconds, _last_movement, _epoch
    with _lock:
        if epoch is not None and epoch != _epoch:
            return
        _action = "IDLE"
        _action_started_at = None
        _action_total_seconds = None
        if movement is not None:
            _last_movement = movement


def get_status() -> dict:
    """Return last movement/action, resolving any timed countdown live."""
    with _lock:
        action, started_at, total = _action, _action_started_at, _action_total_seconds
        last_movement = _last_movement

    if action == "IDLE" or started_at is None:
        return {"last_movement": last_movement, "action": "IDLE", "remaining_seconds": None}

    elapsed = time.monotonic() - started_at
    remaining = max(0, round(total - elapsed)) if total is not None else None
    return {"last_movement": last_movement, "action": action, "remaining_seconds": remaining}
