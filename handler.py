import base64
import io
import os
from typing import Any, Dict
import requests

import runpod
import torch
from PIL import Image


MODEL_PATH = os.environ.get("MODEL_PATH", "")
YOLOV5_DIR = os.environ.get("YOLOV5_DIR", "/app/yolov5")
DEVICE = os.environ.get("DEVICE", "cuda:0" if torch.cuda.is_available() else "cpu")

print(f"Loading YOLOv5 weights from {MODEL_PATH} on {DEVICE}")
model = torch.hub.load(
    YOLOV5_DIR,
    "custom",
    path=MODEL_PATH,
    source="local",
    device=DEVICE,
)
model.eval()

_ = model(Image.new("RGB", (640, 640)))
print("Model ready and warmed up.")


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

    model.conf = confidence
    model.iou = iou

    results = model(image, size=imgsz)
    preds = results.xyxy[0].cpu().tolist()

    detections = []
    for x1, y1, x2, y2, conf, cls_id in preds:
        detections.append({
            "tile": int(cls_id),
            "confidence": float(conf),
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
    runpod.serverless.start({"handler": handler})
