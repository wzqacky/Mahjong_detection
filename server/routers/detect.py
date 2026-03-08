"""
Detection router — sends an uploaded image to Roboflow for YOLOv5 inference
and returns detected mahjong tiles.
"""

import json
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from pydantic import BaseModel, Field

from inference_sdk import InferenceHTTPClient

router = APIRouter(prefix="/api", tags=["detect"])

# Roboflow config — loaded from server/config.json
_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"

_client: Optional[InferenceHTTPClient] = None
_model_id: str = ""


def _load_config() -> dict:
    """Read server/config.json and return its contents."""
    if not _CONFIG_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Config file not found: {_CONFIG_PATH}",
        )
    with open(_CONFIG_PATH) as f:
        return json.load(f)


def _get_client() -> InferenceHTTPClient:
    """Lazy-initialise the Roboflow client from config.json."""
    global _client, _model_id
    if _client is None:
        config = _load_config()
        api_key = config.get("roboflow_api_key", "")
        _model_id = config.get("roboflow_model_id", "")
        if not api_key or api_key == "YOUR_API_KEY_HERE":
            raise HTTPException(
                status_code=500,
                detail="Set roboflow_api_key in server/config.json",
            )
        if not _model_id or _model_id == "YOUR_MODEL_ID_HERE":
            raise HTTPException(
                status_code=500,
                detail="Set roboflow_model_id in server/config.json",
            )
        _client = InferenceHTTPClient(
            api_url="https://detect.roboflow.com",
            api_key=api_key,
        )
    return _client


# Response schema
class Detection(BaseModel):
    """A single detected tile."""
    tile: str = Field(..., description="Tile label, e.g. '5B', 'RD', 'EW'")
    confidence: float = Field(..., description="Detection confidence 0-1")
    x: float = Field(..., description="Bounding-box centre x (pixels)")
    y: float = Field(..., description="Bounding-box centre y (pixels)")
    width: float = Field(..., description="Bounding-box width (pixels)")
    height: float = Field(..., description="Bounding-box height (pixels)")


class DetectResponse(BaseModel):
    """Response from the /api/detect endpoint."""
    detections: List[Detection] = []
    image_width: int = 0
    image_height: int = 0
    error: Optional[str] = None


# Endpoint
@router.post("/detect", response_model=DetectResponse)
async def detect_tiles(
    file: UploadFile = File(..., description="JPEG or PNG image of a mahjong hand"),
    confidence: float = Query(0.4, ge=0.0, le=1.0, description="Minimum confidence threshold"),
):
    """
    Upload an image → get back a list of detected mahjong tiles with positions.
    """
    try:
        client = _get_client()

        image_bytes = await file.read()

        result = client.infer(
            image_bytes,
            model_id=_model_id,
            confidence=confidence,
        )

        detections = [
            Detection(
                tile=pred["class"],
                confidence=pred["confidence"],
                x=pred["x"],
                y=pred["y"],
                width=pred["width"],
                height=pred["height"],
            )
            for pred in result.get("predictions", [])
        ]

        return DetectResponse(
            detections=detections,
            image_width=result.get("image", {}).get("width", 0),
            image_height=result.get("image", {}).get("height", 0),
        )

    except HTTPException:
        raise
    except Exception as exc:
        return DetectResponse(error=str(exc))
