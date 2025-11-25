from ultralytics import YOLO
import config

class CardDetector:
    def __init__(self):
        print(f"Loading YOLO model: {config.YOLO_MODEL}...")
        self.model = YOLO(config.YOLO_MODEL)
        self.names = self.model.names 
        
        # COCO Class IDs we care about:
        # 73: book, 67: cell phone (common misidentification for cards)
        self.allowed_classes = [73, 67] 

    def detect(self, frame):
        height, width = frame.shape[:2]

        # Enable classes filter in YOLO inference directly for speed
        results = self.model(
            frame, 
            imgsz=config.YOLO_INPUT_SIZE, 
            verbose=False, 
            conf=config.CONFIDENCE_THRESHOLD,
            classes=self.allowed_classes # Only return books/phones
        )
        
        valid_boxes = []

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0].cpu().numpy())
                cls = int(box.cls[0].cpu().numpy())
                class_name = self.names[cls]
                
                # RULE 1: EDGE BUFFER
                margin = config.EDGE_MARGIN
                if (x1 < margin or y1 < margin or 
                    x2 > width - margin or y2 > height - margin):
                    continue

                # RULE 2: MINIMUM SIZE
                if ((x2 - x1) < config.MIN_BOX_WIDTH or 
                    (y2 - y1) < config.MIN_BOX_HEIGHT):
                    continue
                
                valid_boxes.append([int(x1), int(y1), int(x2), int(y2), conf, cls, class_name])

        return valid_boxes