FROM ultralytics/ultralytics:latest

# Name the working directory
WORKDIR /app

COPY requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY yolov5/exp/weights/best.pt /app/best.pt
COPY handler.py /app/handler.py

ENV MODEL_PATH=/app/best.pt DEVICE=cuda:0 PYTHONBUFFERED=1

CMD ["python", "-u", "handler.py"]