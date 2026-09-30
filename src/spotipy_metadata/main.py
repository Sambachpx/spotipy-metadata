"""Micro-service de métadonnées audio (TP #11).

Lancement : uv run uvicorn spotipy_metadata.main:app --port 8001
"""

import urllib.parse
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from spotipy_metadata.logic_metadata import extract_metadata

app = FastAPI(title="Metadata micro-service")


class MetadataRead(BaseModel):
    name: str
    duration: int


@app.get("/metadata", response_model=MetadataRead)
@app.get("/api/metadata", response_model=MetadataRead)
def read_metadata(file_path: str) -> MetadataRead:
    path = Path(urllib.parse.unquote(file_path))
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        name, duration = extract_metadata(str(path))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return MetadataRead(name=name, duration=duration)
