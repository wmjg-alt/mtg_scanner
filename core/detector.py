from ultralytics import YOLO
import cv2
import numpy as np
import config

class CardDetector:
    def __init__(self):
        print(f"Loading Custom YOLO model: {config.YOLO_MODEL}...")
        self.model = YOLO(config.YOLO_MODEL)
        self.names = self.model.names 
        # Removed hardcoded 'allowed_classes' because custom models usually 
        # only output what we trained them on.

    def detect(self, frame):
        height, width = frame.shape[:2]

        # 1. RAW INFERENCE
        results = self.model(
            frame, 
            imgsz=config.YOLO_INPUT_SIZE, 
            verbose=False, 
            conf=config.CONFIDENCE_THRESHOLD
            # Removed 'classes' argument
        )
        
        raw_boxes = []
        confidences = []
        class_ids = []

        # 2. EXTRACT DATA
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0].cpu().numpy())
                cls = int(box.cls[0].cpu().numpy())
                
                # Basic validation (Edge & Size)
                margin = config.EDGE_MARGIN
                if (x1 < margin or y1 < margin or 
                    x2 > width - margin or y2 > height - margin):
                    continue

                if ((x2 - x1) < config.MIN_BOX_WIDTH or 
                    (y2 - y1) < config.MIN_BOX_HEIGHT):
                    continue
                
                # Save as [x, y, w, h] for NMS
                w_box = x2 - x1
                h_box = y2 - y1
                
                raw_boxes.append([int(x1), int(y1), int(w_box), int(h_box)])
                confidences.append(float(conf))
                class_ids.append(cls)

        if not raw_boxes:
            return []

        # 3. APPLY NMS
        indices = cv2.dnn.NMSBoxes(
            raw_boxes, 
            confidences, 
            score_threshold=config.CONFIDENCE_THRESHOLD, 
            nms_threshold=config.NMS_THRESHOLD
        )

        final_boxes = []
        
        if len(indices) > 0:
            indices = indices.flatten()
            
            # 4. CONTAINMENT FILTER (Keep it, it's cheap and safe)
            kept_indices = []
            for i in indices:
                boxA = raw_boxes[i] 
                is_contained = False
                areaA = boxA[2] * boxA[3]
                
                for j in indices:
                    if i == j: continue
                    boxB = raw_boxes[j]
                    areaB = boxB[2] * boxB[3]
                    
                    if areaA < areaB:
                        # Calculate Intersection
                        xA = max(boxA[0], boxB[0])
                        yA = max(boxA[1], boxB[1])
                        xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
                        yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])
                        
                        interW = max(0, xB - xA)
                        interH = max(0, yB - yA)
                        intersection = interW * interH
                        
                        if intersection > (areaA * config.CONTAINMENT_THRESHOLD):
                            is_contained = True
                            break
                
                if not is_contained:
                    kept_indices.append(i)

            # 5. FORMAT OUTPUT
            for i in kept_indices:
                x, y, w, h = raw_boxes[i]
                x2 = x + w
                y2 = y + h
                conf = confidences[i]
                cls = class_ids[i]
                name = self.names[cls]
                
                final_boxes.append([x, y, x2, y2, conf, cls, name])

        return final_boxes