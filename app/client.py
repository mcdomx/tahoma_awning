import os

import aiohttp
from dotenv import load_dotenv
from pyoverkiz.client import OverkizClient
from pyoverkiz.const import OverkizServer

load_dotenv()

USERNAME = os.getenv("TAHOMA_USER")
PASSWORD = os.getenv("TAHOMA_PW")
TOKEN = os.getenv("TAHOMA_KEY")
HOST = os.getenv("TAHOMA_HOST")
DEVICE_URL = "rts://1611-2003-9170/16775800"


def make_client() -> OverkizClient:
    session = aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False)
    )
    return OverkizClient(
        username=USERNAME,
        password=PASSWORD,
        token=TOKEN,
        session=session,
        verify_ssl=False,  # local gateway uses a self-signed cert
        server=OverkizServer(
            name="Somfy TaHoma (local)",
            endpoint=f"https://{HOST}:8443/enduser-mobile-web/1/enduserAPI/",
            manufacturer="Somfy",
            configuration_url=None,
        ),
    )
