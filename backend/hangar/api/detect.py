from __future__ import annotations
from pathlib import Path
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.detect import detect_components_in_folder
from ..core.presets import PRESETS

router = APIRouter(prefix="/detect", tags=["detect"])


class DetectRequest(BaseModel):
    path: str


class DetectResponse(BaseModel):
    path: str
    detected_components: list[dict[str, Any]]
    available_presets: list[dict[str, Any]]


@router.post("", response_model=DetectResponse)
async def detect_folder(payload: DetectRequest):
    folder_path = Path(payload.path).resolve()
    if not folder_path.exists():
        raise HTTPException(status_code=400, detail=f"Path does not exist: {folder_path}")
    if not folder_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {folder_path}")

    detected = detect_components_in_folder(folder_path)
    return DetectResponse(
        path=str(folder_path),
        detected_components=detected,
        available_presets=PRESETS,
    )

