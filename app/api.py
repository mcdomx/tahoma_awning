from fastapi import FastAPI, HTTPException

from app.commands import (
    deploy_awning,
    get_devices,
    my_position,
    stop_awning,
    undeploy_awning,
)

app = FastAPI(title="Tahoma Awning API")


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
