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
from PIL import Image, ImageDraw, ImageFont

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


CJK_FONT_PATH = os.environ.get("CJK_FONT_PATH", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")


class MahjongTileDetector:
    def __init__(self,
                 weights,
                 output_dir,
                 img_size=640,
                 conf_thres=0.25,
                 iou_thres=0.45,
                 show_zh=False,
                 ):
        self.weights = weights
        self.device = select_device()
        self.output_dir = output_dir
        self.img_size = img_size
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres
        self.show_zh = show_zh

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

    def _plot_boxes(self, im, img0, det):
        num_classes = len(self.name)

        # Generate random color for each class
        np.random.seed(42)
        colors = {i: tuple(int(c) for c in color) for i, color in
              enumerate(np.random.randint(0, 255, size=(num_classes, 3)))}

        img_pil = Image.fromarray(cv2.cvtColor(img0, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        if self.show_zh:
            if not os.path.exists(CJK_FONT_PATH):
                print("show_zh activated, but no default Chinese font path found, disabling it."
                      "Change the environment variable 'CJK_FONT_PATH' to a Chinese font.")
                self.show_zh = False
            else:
                font = ImageFont.truetype(CJK_FONT_PATH, size=18)
        else:
            font = ImageFont.load_default()

        for *xyxy, conf, cls in det:
            x1, y1, x2, y2 = [int(v.item()) for v in xyxy]
            cls_id = int(cls.item())
            confidence = conf.item()
            bgr = colors.get(cls_id, (0, 255, 0))
            rgb = (bgr[2], bgr[1], bgr[0])
            label = (f"{self.name_to_zh[self.name[cls_id]]} {confidence:.2f}"
                     if self.show_zh else f"{self.name[cls_id]} {confidence:.2f}")

            # Bounding box
            draw.rectangle([x1, y1, x2, y2], outline=rgb, width=2)

            # Label background + Text
            left, top, right, bottom = draw.textbbox((x1, y1), label, font=font)
            tw, th = right - left, bottom - top
            draw.rectangle([x1, y1 - th - 6, x1 + tw + 4, y1], fill=rgb)
            draw.text((x1 + 2, y1 - th - 4), label, fill=(255, 255, 255), font=font)
        
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def _get_zh_names(self):
        return {
            "1D": "一筒", "2D": "二筒", "3D": "三筒", "4D": "四筒", "5D": "五筒",
            "6D": "六筒", "7D": "七筒", "8D": "八筒", "9D": "九筒",

            "1B": "一索", "2B": "二索", "3B": "三索", "4B": "四索", "5B": "五索",
            "6B": "六索", "7B": "七索", "8B": "八索", "9B": "九索",

            "1C": "一萬", "2C": "二萬", "3C": "三萬", "4C": "四萬", "5C": "五萬",
            "6C": "六萬", "7C": "七萬", "8C": "八萬", "9C": "九萬",

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
            tiles = []
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
                    tiles.append(self.name[cls_id])
                    confidence = conf.item()
                    f.write(f"{cls_id} {x_center:.6f}, {y_center:.6f}, {bw:.6f}, {bh:.6f}, {confidence:.6f}\n")
            
            # Get visualization
            img_vis = self._plot_boxes(im, img0, det)
            cv2.imwrite(str(vis_file), img_vis)
            print(f"{img_name}: {len(det)} detections")

            print(f"Labels saved to: {str(label_file)}")
            print(f"Visualizations saved to: {str(vis_file)}")
            return tiles
    
    def detect(self, img_path):
        im, img0 = self._load_image(img_path)
        im = self._process_image(im)
        
        pred = self._model(im)

        # Process detections
        tiles = self.process_pred(pred, im, img0, img_path)

        return tiles


def run(
        weights,
        input_img_path,
        output_dir,
        img_size,
        conf_thres,
        iou_thres,
        show_zh
):
    # TODO: Have to support arbitrary image size
    detector = MahjongTileDetector(weights=weights, 
                                   output_dir=output_dir,
                                   img_size=img_size,
                                   conf_thres=conf_thres,
                                   iou_thres=iou_thres,
                                   show_zh=show_zh)
    detector.detect(input_img_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run YOLOv5 inference and save predicted labels")
    parser.add_argument("--weights", type=str, required=True,
                        help="Path to model weights")
    parser.add_argument("--input_img_path", type=str, required=True,
                        help="Path to the testing image")
    parser.add_argument("--output_dir", type=str, default="testing/predicted_labels",
                        help="Directory to save predicted labels")
    parser.add_argument("--img_size", type=int, default=640, help="inference image size")
    parser.add_argument("--conf_thres", type=float, default=0.25, help="confidence threshold")
    parser.add_argument("--iou_thres", type=float, default=0.45, help="NMS IoU threshold")
    parser.add_argument("--show_zh", action="store_true", help="Whether to show Chinese labels.")
    args = parser.parse_args()

    run(
        weights=args.weights,
        input_img_path=args.input_img_path,
        output_dir=args.output_dir,
        img_size=args.img_size,
        conf_thres=args.conf_thres,
        iou_thres=args.iou_thres,
        show_zh=args.show_zh
    )
