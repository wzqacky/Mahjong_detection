"""
Test script for Mahjong tile detection.
Runs inference on dataset/mahjong/test/images using the trained YOLOv5 model
and saves predicted labels in YOLO format.
"""

import argparse
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import torch

# Add YOLOv5 to path
FILE = Path(__file__).resolve()
ROOT = FILE.parent
YOLO_ROOT = ROOT / "yolov5"
if str(YOLO_ROOT) not in sys.path:
    sys.path.insert(0, str(YOLO_ROOT))

from models.common import DetectMultiBackend
from utils.dataloaders import LoadImages
from utils.general import non_max_suppression, scale_boxes, check_img_size
from utils.augmentations import letterbox
from utils.torch_utils import select_device

class MahjongTileDetector:
    def __init__(self,
                 weights,
                 output_dir,
                 img_size=640,
                 conf_thres=0.25,
                 iou_thres=0.45,
                 ):
        self.weights = weights
        self.device = select_device()
        self.output_dir = output_dir
        self.img_size = img_size
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres

        self._setup()

    def _setup(self):
        self.model = DetectMultiBackend(self.weights, device=self.device)
        self.stride = self.model.stride
        self.name = self.model.names
        self.name_to_zh = self._get_zh_names()
        self.pt = self.model.pt
        self.img_size = check_img_size(self.img_size, s=self.stride)

    def _load_image(self, img_path):
        img0 = cv2.imread(img_path)
        assert img0 is not None, f"Image Not Found: {img_path}"
        # TODO: What the heck is this letterbox
        im = letterbox(img0, self.img_size, stride=self.stride, auto=True)[0]
        im = im.transpose((2,0,1))[::-1] # hwc -> chw, bgr -> rgb
        im = np.ascontiguousarray(im) # Make contiguous
        return im, img0
    
    def _process_image(self, im):
        im = torch.from_numpy(im).to(self.device)
        im = im.float() / 255.0
        if im.ndimension() == 3:
            im = im.unsqueeze(0) # Make ndimension = 4
        return im
    
    def _model(self, im):
        pred = self.model(im)
        # NMS
        pred = non_max_suppression(pred, self.conf_thres, self.iou_thres)
        return pred

    def _plot_boxes(self, im, img0, det, show_zh=True):
        img_draw = img0.copy()
        num_classes = len(self.name)

        # Generate random color for each class
        np.random.seed(42)
        colors = {i: tuple(int(c) for c in color) for i, color in
              enumerate(np.random.randint(0, 255, size=(num_classes, 3)))}
    
        for *xyxy, conf, cls in det:
            x1, y1, x2, y2 = [int(v.item()) for v in xyxy]

            cls_id = int(cls.item())
            confidence = conf.item()
            color = colors.get(cls_id, (0, 255, 0))
            label = f"{self.name[cls_id]} {confidence:.2f}" if not show_zh else \
                f"{self.name_to_zh[self.name[cls_id]]} {confidence:.2f}"

            # Draw bounding boxes
            cv2.rectangle(img_draw, (x1, y1), (x2, y2), color, 2)

            # Draw label background
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(img_draw, (x1, y1 - th - 6), (x1 + tw, y1), color, -1)
            cv2.putText(img_draw, label, (x1, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        return img_draw

    def _get_zh_names(self):
        return {
            "1B": "一筒", "2B": "二筒", "3B": "三筒", "4B": "四筒", "5B": "五筒",
            "6B": "六筒", "7B": "七筒", "8B": "八筒", "9B": "九筒",

            "1C": "一索", "2C": "二索", "3C": "三索", "4C": "四索", "5C": "五索",
            "6C": "六索", "7C": "七索", "8C": "八索", "9C": "九索",

            "1D": "一萬", "2D": "二萬", "3D": "三萬", "4D": "四萬", "5D": "五萬",
            "6D": "六萬", "7D": "七萬", "8D": "八萬", "9D": "九萬",

            "EW": "東", "SW": "南", "WW": "西", "NW": "北",
            "WD": "白", "GD": "發", "RD": "中",

            "1F": "梅", "2F": "蘭", "3F": "竹", "4F": "菊",
            "1S": "春", "2S": "夏", "3S": "秋", "4S": "冬"
        }

    def process_pred(self, pred, im, img0, img_path):
        img_name = Path(img_path).stem
        output_dir = Path(self.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        label_file = Path(self.output_dir)/f"{img_name}.txt"
        vis_file = Path(self.output_dir)/f"{img_name}_vis.jpg"
        
        h, w = img0.shape[:2]

        for det in pred:
            if not len(det):
                # Save original image (no detection found)
                cv2.imwrite(str(vis_file), img0)
                print(f"{img_name}: No detections")
                continue

            # Rescale boxes from img_size to original image size
            det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], img0.shape).round()

            # Write results in YOLO format: (class, x_center, y_center, width, height)
            with open(label_file, "w") as f:
                for *xyxy, conf, cls in det:
                    x1, y1, x2, y2 = [v.item() for v in xyxy]
                    x_center = ((x1+x2) / 2) / w
                    y_center = ((y1+y2) / 2) / h
                    bw = (x2 - x1) / w
                    bh = (y2 - y1) / h
                    cls_id = int(cls.item())
                    confidence = conf.item()
                    f.write(f"{cls_id} {x_center:.6f}, {y_center:.6f}, {bw:.6f}, {bh:.6f}, {confidence:.6f}\n")
            
            # Get visualization
            img_vis = self._plot_boxes(im, img0, det)
            cv2.imwrite(str(vis_file), img_vis)
            print(f"{img_name}: {len(det)} detections")

            print(f"Labels saved to: {str(label_file)}")
            print(f"Visualizations saved to: {str(vis_file)}")
    
    def detect(self, img_path):
        im, img0 = self._load_image(img_path)
        im = self._process_image(im)
        
        pred = self._model(im)

        # Process detections
        self.process_pred(pred, im, img0, img_path)


def run(
        weights,
        input_img_path,
        output_dir,
        img_size,
        conf_thres,
        iou_thres,
):
    # TODO: Have to support arbitrary image size
    detector = MahjongTileDetector(weights=weights, 
                                   output_dir=output_dir,
                                   img_size=img_size,
                                   conf_thres=conf_thres,
                                   iou_thres=iou_thres)
    detector.detect(input_img_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run YOLOv5 inference and save predicted labels")
    parser.add_argument("--weights", type=str, required=True,
                        help="Path to model weights")
    parser.add_argument("--input_img_path", type=str, required=True,
                        help="Path to the testing image")
    parser.add_argument("--output_dir", type=str, default="test/predicted_labels",
                        help="Directory to save predicted labels")
    parser.add_argument("--img_size", type=int, default=640, help="inference image size")
    parser.add_argument("--conf_thres", type=float, default=0.25, help="confidence threshold")
    parser.add_argument("--iou_thres", type=float, default=0.45, help="NMS IoU threshold")
    args = parser.parse_args()

    run(
        weights=args.weights,
        input_img_path=args.input_img_path,
        output_dir=args.output_dir,
        img_size=args.img_size,
        conf_thres=args.conf_thres,
        iou_thres=args.iou_thres,
    )
