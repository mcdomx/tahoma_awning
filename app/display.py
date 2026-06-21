"""Optional I2C 1602 LCD status display.

Drives a Hosyond (PCF8574-backpack) 16x2 character LCD attached to a
Raspberry Pi, showing the tracked awning status and current action. The
display is entirely optional: if the LCD library is missing, the hardware
is absent, or the I2C bus errors at runtime, the application keeps running
normally — every hardware path is guarded and never raises into the caller.

Fixed 16x2 layout::

    STATUS: DEPLOYED     line 1: "STATUS: " + tracked position
    DEPLOYING 12S        line 2: current action (IDLE / DEPLOYING Ns / RETRACTING Ns)
"""

import logging
import os
import threading
import time
from typing import Tuple

from app.state import get_status

try:
    from RPLCD.i2c import CharLCD

    _LIB_AVAILABLE = True
except ImportError:
    CharLCD = None  # type: ignore[assignment, misc]
    _LIB_AVAILABLE = False

logger = logging.getLogger(__name__)

LCD_COLS: int = 16
LCD_ROWS: int = 2

_started = threading.Event()


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _pad(line: str) -> str:
    """Truncate/pad a line to exactly LCD_COLS characters."""
    return line[:LCD_COLS].ljust(LCD_COLS)


def format_lines(status: dict) -> Tuple[str, str]:
    """Build the two LCD rows from current state. Pure; no hardware access."""
    line1 = _pad(f"STATUS: {status['position']}")

    action = status["action"]
    if action == "IDLE":
        line2 = "IDLE"
    elif status["remaining_seconds"] is not None:
        line2 = f"{action} {status['remaining_seconds']}S"
    else:
        line2 = action
    return line1, _pad(line2)


def _init_lcd():
    """Create and return a CharLCD handle, or raise if it cannot be opened."""
    address = int(os.getenv("LCD_I2C_ADDRESS", "0x27"), 0)
    port = _env_int("LCD_I2C_PORT", 1)
    lcd = CharLCD(
        i2c_expander="PCF8574",
        address=address,
        port=port,
        cols=LCD_COLS,
        rows=LCD_ROWS,
        auto_linebreaks=False,
    )
    lcd.clear()
    return lcd


def _display_thread(lcd) -> None:
    interval = _env_int("LCD_UPDATE_SECONDS", 1)
    prev = None
    while True:
        lines = format_lines(get_status())
        if lines != prev:
            try:
                lcd.cursor_pos = (0, 0)
                lcd.write_string(lines[0])
                lcd.cursor_pos = (1, 0)
                lcd.write_string(lines[1])
                prev = lines
            except Exception:
                logger.exception("LCD write failed; disabling display")
                return
        time.sleep(interval)


def start_display() -> None:
    """Start the LCD render loop if a display is enabled and available.

    Safe to call unconditionally: returns quietly (logging the reason) when the
    display is disabled, the library is missing, or the LCD cannot be opened.
    """
    if _started.is_set():
        return

    mode = os.getenv("LCD_ENABLED", "auto").lower()
    if mode in ("false", "0", "no", "off"):
        logger.info("LCD display disabled via LCD_ENABLED")
        return

    if not _LIB_AVAILABLE:
        logger.info("LCD library (RPLCD) not installed; running without display")
        return

    try:
        lcd = _init_lcd()
    except Exception:
        logger.info("LCD not detected on I2C bus; running without display")
        return

    _started.set()
    t = threading.Thread(target=_display_thread, args=(lcd,), daemon=True, name="lcd-display")
    t.start()
    logger.info("LCD display started")
