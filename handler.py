import base64
import io
import os
from typing import Any, Dict
import requests

import runpod
from PIL import Image
from ultralytics import YOLO


MODEL_PATH = os.environ.get("MODEL_PATH", "")
DEVICE = os.environ.get("DEVICE", "cuda:0") # falls back to cpu on cpu workers

print(f"Loading YOLO weights from {MODEL_PATH} on {DEVICE}")
model = YOLO(MODEL_PATH)

_ = model.predict(
    Image.new("RGB", (640, 640)),
    device=DEVICE,
    verbose=False,
)
print(f"Model ready and warmed up.")


def _load_image(job_input: Dict[str, Any]) -> Image.Image:
    """
    Accept either base64 or a URL and returns a PIL image.
    """
    if "image_b64" in job_input:
        raw = base64.b64decode(job_input["image_b64"])
        return Image.open(io.BytesIO(raw)).convert("RGB")

    if "image_url" in job_input:
        resp = requests.get(job_input["image_url"], timeout=15)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content)).convert("RGB")
    raise ValueError("Input must contain 'image_b64' or 'image_url'.")


def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    job_input = job.get("input", {}) or {}
    confidence = float(job_input.get("confidence", 0.4))
    iou = float(job_input.get("iou", 0.45))
    imgsz = int(job_input.get("imgsz", 640))

    try:
        image = _load_image(job_input)
    except Exception as e:
        return {"error": f"Failed to load image: {e}"}

    results = model.predict(
        image,
        conf=confidence,
        iou=iou,
        imgsz=imgsz,
        device=DEVICE,
        verbose=False,
    )
    r = results[0]

    names = r.names
    detections = []
    for box in r.boxes:
        cls_id = int(box.cls[0].item())
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        detections.append({
            "tile": cls_id,
            "confidence": float(box.conf[0].item()),
            "x": (x1 + x2) / 2,
            "y": (y1 + y2) / 2,
            "width": x2 - x1,
            "height": y2 - y1,
        })

    return {
        "detections": detections,
        "image_width": int(image.width),
        "image_height": int(image.height),
    }


if __name__ == "__main__":
    runpod.serveless.start({"handler": handler})
