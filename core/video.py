import cv2
from PySide6.QtCore import QThread, Signal
import numpy as np
from core.detector import CardDetector
from core.tracker import CentroidTracker
import config

class VideoThread(QThread):
    change_pixmap_signal = Signal(np.ndarray)
    debug_info_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.detector = None 
        self.tracker = CentroidTracker() 

    def run(self):
        # Initialize Camera
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.REQUEST_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.REQUEST_HEIGHT)

        # Initialize Detector
        if self.detector is None:
            self.detector = CardDetector()

        frame_count = 0
        
        while self._run_flag:
            ret, frame = cap.read()
            if ret:
                h, w = frame.shape[:2]
                frame_count += 1
                
                # --- 1. DETECTION & TRACKING ---
                rects = []
                confidences = [] # Store confidences for debug display
                
                # Only run YOLO every N frames
                if frame_count % config.DETECT_EVERY_N_FRAMES == 0:
                    detections = self.detector.detect(frame)
                    
                    for item in detections:
                        # item = [x1, y1, x2, y2, conf, cls, name]
                        rects.append(item[0:4]) 
                        confidences.append(item[4])
                    
                    # Update Tracker with new positions
                    objects = self.tracker.update(rects)
                    
                    # Custom Debug String (Requested by you)
                    if objects:
                        conf_str = [round(c, 2) for c in confidences]
                        debug_str = f"Tracking {len(objects)} Cards | IDs: {list(objects.keys())} | Conf: {conf_str}"
                    else:
                        debug_str = "Tracking: None"
                    
                    self.debug_info_signal.emit(debug_str)
                
                else:
                    # In skipped frames, just use existing tracker data
                    objects = self.tracker.objects

                # --- 2. DRAWING & DEBUGGING ---
                # Loop through tracked objects
                for (objectID, centroid) in objects.items():
                    # Only draw if we still have a valid bounding box
                    if objectID in self.tracker.bboxes:
                        box = self.tracker.bboxes[objectID]
                        (x1, y1, x2, y2) = box
                        
                        # Draw Box (Green)
                        if config.SHOW_DEBUG_BOXES:
                            cv2.rectangle(frame, (x1, y1), (x2, y2), config.DEBUG_COLOR_BOX, 2)

                        # Draw ID and Centroid (Red)
                        text = f"ID {objectID}"
                        cv2.putText(frame, text, (centroid[0] - 10, centroid[1] - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 2.5, (0, 0, 255), 2)
                        cv2.circle(frame, (centroid[0], centroid[1]), 4, (0, 0, 255), -1)

                        # Draw Search Radius (Yellow)
                        if config.SHOW_DEBUG_BOXES:
                            cv2.circle(frame, (centroid[0], centroid[1]), 
                                       config.MAX_TRACKING_DISTANCE, (0, 255, 255), 1)

                        # Draw Trails
                        if objectID in self.tracker.history:
                            history = self.tracker.history[objectID]
                            for i in range(1, len(history)):
                                if history[i - 1] is None or history[i] is None: continue
                                cv2.line(frame, history[i - 1], history[i], (0, 0, 255), 2)

                # Draw Safety Border (Red)
                if config.SHOW_EDGE_BORDER:
                    m = config.EDGE_MARGIN
                    cv2.rectangle(frame, (m, m), (w-m, h-m), config.DEBUG_COLOR_BORDER, 2)

                self.change_pixmap_signal.emit(frame)
            
            # Tiny sleep to prevent CPU hogging
            self.msleep(10)

        cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()