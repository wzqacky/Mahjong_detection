FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        git libglib2.0-0 libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY yolov5/requirements.txt /app/yolov5-requirements.txt
RUN pip install --no-cache-dir -r /app/yolov5-requirements.txt

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY yolov5 /app/yolov5
COPY checkpoints/best.pt /app/best.pt
COPY handler.py /app/handler.py

ENV MODEL_PATH=/app/best.pt \
    YOLOV5_DIR=/app/yolov5 \
    DEVICE=cuda:0 \
    PYTHONUNBUFFERED=1

CMD ["python", "-u", "handler.py"]
