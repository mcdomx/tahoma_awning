import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query

from app.commands import (
    deploy_awning,
    deploy_for_seconds,
    get_devices,
    my_position,
    stop_awning,
    undeploy_awning,
    undeploy_for_seconds,
)
from app.display import start_display


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        start_display()
    except Exception:
        logging.exception("LCD display failed to start; continuing without it")
    yield


app = FastAPI(title="Tahoma Awning API", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/awning/deploy")
async def deploy() -> dict:
    try:
        await deploy_awning()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/awning/undeploy")
async def undeploy() -> dict:
    try:
        await undeploy_awning()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/awning/deploy/timed")
async def deploy_timed(seconds: float = Query(..., gt=0, description="Seconds to deploy before stopping")) -> dict:
    try:
        await deploy_for_seconds(seconds)
        return {"status": "ok", "seconds": seconds}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/awning/undeploy/timed")
async def undeploy_timed(seconds: float = Query(..., gt=0, description="Seconds to retract before stopping")) -> dict:
    try:
        await undeploy_for_seconds(seconds)
        return {"status": "ok", "seconds": seconds}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/awning/stop")
async def stop() -> dict:
    try:
        await stop_awning()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/awning/my")
async def my() -> dict:
    try:
        await my_position()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/awning/devices")
async def devices() -> list:
    try:
        result = await get_devices()
        return [
            {
                "url": d.device_url,
                "label": d.label,
                "type": d.controllable_name,
            }
            for d in result
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
