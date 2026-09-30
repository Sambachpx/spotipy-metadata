"""Micro-service de métadonnées audio (TP #11 + TP #12 message bus).

Lancement : uv run uvicorn spotipy_metadata.main:app --port 8001
Nécessite un broker MQTT joignable (docker compose : service mqtt).
"""

import json
import os
import time
import urllib.parse
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi_mqtt import FastMQTT, MQTTConfig
from pydantic import BaseModel

from spotipy_metadata.logic_metadata import extract_metadata

mqtt_config = MQTTConfig(
    host=os.getenv("MQTT_HOST", "localhost"),
    port=int(os.getenv("MQTT_PORT", "1883")),
)
fast_mqtt = FastMQTT(config=mqtt_config)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Démarre la connexion MQTT puis la coupe à l'arrêt."""
    await fast_mqtt.mqtt_startup()
    try:
        yield
    finally:
        await fast_mqtt.mqtt_shutdown()


app = FastAPI(title="Metadata micro-service", lifespan=lifespan)


class MetadataRead(BaseModel):
    name: str
    duration: int


@app.get("/metadata", response_model=MetadataRead)
@app.get("/api/metadata", response_model=MetadataRead)
def read_metadata(file_path: str) -> MetadataRead:
    path = Path(urllib.parse.unquote(file_path))
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    started = time.perf_counter()
    try:
        name, duration = extract_metadata(str(path))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    analyze_duration = int((time.perf_counter() - started) * 1000)

    # Notifie le bus pour le micro-service stats (TP #12).
    payload = json.dumps(
        {
            "title": name,
            "filename": path.name,
            "duration": duration,
            "analyze_at": datetime.now(UTC).isoformat(),
            "analyze_duration": analyze_duration,
        }
    )
    fast_mqtt.publish("metadata/song-analyzed", payload)

    return MetadataRead(name=name, duration=duration)
