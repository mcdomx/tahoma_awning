import asyncio

from pyoverkiz.models import Command

from app.client import DEVICE_URL, make_client


async def deploy_awning() -> None:
    async with make_client() as client:
        await client.login()
        await client.execute_command(DEVICE_URL, Command("deploy", []))


async def undeploy_awning() -> None:
    async with make_client() as client:
        await client.login()
        await client.execute_command(DEVICE_URL, Command("undeploy", []))


async def stop_awning() -> None:
    async with make_client() as client:
        await client.login()
        await client.execute_command(DEVICE_URL, Command("stop", []))


async def my_position() -> None:
    async with make_client() as client:
        await client.login()
        await client.execute_command(DEVICE_URL, Command("my", []))


async def deploy_for_seconds(seconds: float) -> None:
    await deploy_awning()
    await asyncio.sleep(seconds)
    await stop_awning()


async def undeploy_for_seconds(seconds: float) -> None:
    await undeploy_awning()
    await asyncio.sleep(seconds)
    await stop_awning()


async def get_devices() -> list:
    async with make_client() as client:
        await client.login()
        return await client.get_devices()
