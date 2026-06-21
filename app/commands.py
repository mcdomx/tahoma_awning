import asyncio
import os

from pyoverkiz.models import Command

from app.client import DEVICE_URL, make_client
from app.state import end_action, start_action


def _travel_seconds() -> float:
    return float(os.getenv("AWNING_TRAVEL_SECONDS", "25"))


def _format_seconds(seconds: float) -> str:
    return f"{int(seconds)}s" if seconds == int(seconds) else f"{seconds:g}s"


async def _send_command(command: str) -> None:
    async with make_client() as client:
        await client.login()
        await client.execute_command(DEVICE_URL, Command(command, []))


async def deploy_awning() -> None:
    travel = _travel_seconds()
    epoch = start_action("DEPLOYING", total_seconds=travel)
    await _send_command("deploy")
    asyncio.create_task(_auto_settle(travel, "FULLY DEPLOYED", epoch))


async def undeploy_awning() -> None:
    travel = _travel_seconds()
    epoch = start_action("RETRACTING", total_seconds=travel)
    await _send_command("undeploy")
    asyncio.create_task(_auto_settle(travel, "FULLY RETRACTED", epoch))


async def stop_awning() -> None:
    """Stop is not a movement: the last recorded movement stays on the LCD."""
    await _send_command("stop")
    end_action()


async def my_position() -> None:
    await _send_command("my")
    end_action()


async def deploy_for_seconds(seconds: float) -> None:
    start_action("DEPLOYING", total_seconds=seconds)
    await _send_command("deploy")
    await asyncio.sleep(seconds)
    await _send_command("stop")
    end_action(f"DEPLOYED {_format_seconds(seconds)}")


async def undeploy_for_seconds(seconds: float) -> None:
    start_action("RETRACTING", total_seconds=seconds)
    await _send_command("undeploy")
    await asyncio.sleep(seconds)
    await _send_command("stop")
    end_action(f"RETRACTED {_format_seconds(seconds)}")


async def _auto_settle(travel_seconds: float, movement: str, epoch: int) -> None:
    """Flip action back to IDLE once the awning's full travel time has elapsed.

    The RTS device gives no completion feedback, so this is an estimate based
    on AWNING_TRAVEL_SECONDS rather than an actual position read. No-ops if a
    newer command (e.g. stop) has already changed the state.
    """
    await asyncio.sleep(travel_seconds)
    end_action(movement, epoch=epoch)


async def get_devices() -> list:
    async with make_client() as client:
        await client.login()
        return await client.get_devices()
