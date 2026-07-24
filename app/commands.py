import asyncio
import time

from pyoverkiz.models import Command

from app.client import DEVICE_URL, make_client
from app.state import (
    end_action,
    format_seconds,
    get_action_info,
    get_position,
    set_position,
    start_action,
    travel_seconds,
)


def _clamp_position(seconds: float) -> float:
    return max(0.0, min(travel_seconds(), seconds))


async def _send_command(command: str) -> None:
    async with make_client() as client:
        await client.login()
        await client.execute_command(DEVICE_URL, Command(command, []))


async def deploy_awning() -> None:
    travel = travel_seconds()
    epoch = start_action("DEPLOYING", total_seconds=travel)
    await _send_command("deploy")
    asyncio.create_task(_auto_settle(travel, f"Deploy {format_seconds(travel)}", epoch, final_position=travel))


async def undeploy_awning() -> None:
    travel = travel_seconds()
    epoch = start_action("RETRACTING", total_seconds=travel)
    await _send_command("undeploy")
    asyncio.create_task(_auto_settle(travel, f"Retract {format_seconds(travel)}", epoch, final_position=0.0))


async def stop_awning() -> None:
    """If stop interrupts an active deploy/undeploy, record it as a movement
    (e.g. "Deploy 2s") so the LCD matches /awning/state. A stop with no
    active move (e.g. pressed while already IDLE) leaves the LCD unchanged.
    """
    info = get_action_info()
    movement = None
    if info["action"] in ("DEPLOYING", "RETRACTING") and info["started_at"] is not None:
        elapsed = time.monotonic() - info["started_at"]
        start_position = info["start_position"] if info["start_position"] is not None else 0.0
        delta = elapsed if info["action"] == "DEPLOYING" else -elapsed
        set_position(_clamp_position(start_position + delta))
        verb = "Deploy" if info["action"] == "DEPLOYING" else "Retract"
        movement = f"{verb} {format_seconds(elapsed)}"
    await _send_command("stop")
    end_action(movement)


async def my_position() -> None:
    await _send_command("my")
    set_position(None)  # preset position, distance from either end is unknown
    end_action()


async def deploy_for_seconds(seconds: float) -> None:
    start_action("DEPLOYING", total_seconds=seconds)
    start_position = get_position() or 0.0
    await _send_command("deploy")
    await asyncio.sleep(seconds)
    await _send_command("stop")
    set_position(_clamp_position(start_position + seconds))
    end_action(f"Deploy {format_seconds(seconds)}")


async def undeploy_for_seconds(seconds: float) -> None:
    start_action("RETRACTING", total_seconds=seconds)
    start_position = get_position() or 0.0
    await _send_command("undeploy")
    await asyncio.sleep(seconds)
    await _send_command("stop")
    set_position(_clamp_position(start_position - seconds))
    end_action(f"Retract {format_seconds(seconds)}")


async def _auto_settle(duration_seconds: float, movement: str, epoch: int, final_position: float) -> None:
    """Flip action back to IDLE once the awning's full travel time has elapsed.

    The RTS device gives no completion feedback, so this is an estimate based
    on AWNING_TRAVEL_SECONDS rather than an actual position read. No-ops if a
    newer command (e.g. stop) has already changed the state.
    """
    await asyncio.sleep(duration_seconds)
    if end_action(movement, epoch=epoch):
        set_position(final_position)


async def get_devices() -> list:
    async with make_client() as client:
        await client.login()
        return await client.get_devices()
