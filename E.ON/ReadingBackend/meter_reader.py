import cv2
import numpy as np
from ultralytics import YOLO

class GasMeterReader:
    def __init__(self, box_model_path='best.pt', digit_model_path='yolo_digits.pt'):
        print("Initializing AI Models... Please wait.")
        self.box_model = YOLO(box_model_path)
        self.digit_model = YOLO(digit_model_path)
        print("AI Models Loaded Successfully!")

    def process_image(self, img_array):
        # --- STAGE 1: FIND AND CROP THE INDEX BOX ---
        box_results = self.box_model(img_array, conf=0.05, verbose=False) 

        if len(box_results[0].boxes) == 0:
            return None

        box = box_results[0].boxes[0]
        x1, y1, x2, y2 = map(int, box.xyxy[0]) 

        box_height = y2 - y1
        box_width = x2 - x1

        # Shave top/bottom 5%, shave sides 4% to remove plastic ghosting
        y1 = y1 + int(box_height * 0.05) 
        y2 = y2 - int(box_height * 0.05) 
        x1 = x1 + int(box_width * 0.04) 
        x2 = x2 - int(box_width * 0.04) 

        y1, y2 = max(0, y1), min(img_array.shape[0], y2)
        x1, x2 = max(0, x1), min(img_array.shape[1], x2)

        perfect_crop = img_array[y1:y2, x1:x2]

        # --- STAGE 2: READ THE DIGITS ---
        large_crop = cv2.resize(perfect_crop, None, fx=3.0, fy=3.0, interpolation=cv2.INTER_LINEAR)
        digit_results = self.digit_model(large_crop, conf=0.1, iou=0.2, verbose=False)

        raw_digits = []
        for d_box in digit_results[0].boxes:
            d_x1, d_y1, d_x2, d_y2 = map(int, d_box.xyxy[0])
            class_id = int(d_box.cls[0].item()) 
            digit_name = self.digit_model.names[class_id] 
            conf_score = float(d_box.conf[0].item()) 
            
            x_center = (d_x1 + d_x2) / 2.0
            width = d_x2 - d_x1
            
            raw_digits.append({
                'digit': digit_name,
                'conf': conf_score,
                'x_center': x_center,
                'width': width
            })

        raw_digits.sort(key=lambda x: x['x_center'])

        # --- OVERLAP FILTER ---
        filtered_digits = []
        for current in raw_digits:
            if len(filtered_digits) == 0:
                filtered_digits.append(current)
            else:
                last = filtered_digits[-1]
                if (current['x_center'] - last['x_center']) < (last['width'] * 0.5):
                    if current['conf'] > last['conf']:
                        filtered_digits[-1] = current 
                else:
                    filtered_digits.append(current)

        if len(filtered_digits) == 0:
            return None

        final_reading = "".join([d['digit'] for d in filtered_digits])
        return final_reading