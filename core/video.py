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
        self.tracker = CentroidTracker() # Initialize Tracker

    def run(self):
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.REQUEST_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.REQUEST_HEIGHT)

        if self.detector is None:
            self.detector = CardDetector()

        frame_count = 0
        
        while self._run_flag:
            ret, frame = cap.read()
            if ret:
                h, w = frame.shape[:2]
                frame_count += 1
                
                # 1. DETECT (Run YOLO occasionally)
                # We initialize rects list. If we don't detect this frame, we pass empty list? 
                # No, Tracker needs constant updates or it thinks things disappeared.
                # Ideally, we track every frame, but detect every N frames.
                # For Phase 3 simplicity: We will only update tracker when we detect.
                # (Later we can add optical flow for in-between frames if needed)
                
                rects = []
                detected_objects = [] # For debug text
                
                if frame_count % config.DETECT_EVERY_N_FRAMES == 0:
                    detections = self.detector.detect(frame)
                    
                    # Strip out just the box coordinates for the tracker
                    for item in detections:
                        # item = [x1, y1, x2, y2, conf, cls, name]
                        rects.append(item[0:4]) 
                        detected_objects.append(f"{item[6]}")

                    # 2. TRACK (Update IDs)
                    objects = self.tracker.update(rects)
                    
                    # Update Debug Text
                    if objects:
                        debug_str = f"Tracking {len(objects)} Cards | IDs: {list(objects.keys())}"
                    else:
                        debug_str = "Tracking: None"
                    self.debug_info_signal.emit(debug_str)

                else:
                    # In between detection frames, use the cached objects from the tracker
                    objects = self.tracker.objects

                # 3. DRAW DEBUG INFO
                for (objectID, centroid) in objects.items():
                    if objectID in self.tracker.bboxes:
                        box = self.tracker.bboxes[objectID]
                        (x1, y1, x2, y2) = box
                        
                        # A. Draw Box
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                        # B. Draw ID 
                        text = f"ID {objectID}"
                        cv2.putText(frame, text, (centroid[0] - 10, centroid[1] - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2)
                        
                        # C. Draw Centroid
                        cv2.circle(frame, (centroid[0], centroid[1]), 4, (0, 0, 255), -1)

                        # --- NEW: Draw Search Radius ---
                        # This helps visualize "MAX_TRACKING_DISTANCE"
                        # If the card moves out of this circle in one 'tick', ID is lost.
                        cv2.circle(frame, (centroid[0], centroid[1]), config.MAX_TRACKING_DISTANCE, (0, 255, 255), 1)

                        # D. Draw Trail
                        if objectID in self.tracker.history:
                            history = self.tracker.history[objectID]
                            for i in range(1, len(history)):
                                # Connect points with a line
                                ptA = history[i - 1]
                                ptB = history[i]
                                # Check if points are valid (not 0,0)
                                if ptA is None or ptB is None: continue
                                cv2.line(frame, ptA, ptB, (0, 0, 255), 2)

                # Draw Edge Buffer
                if config.SHOW_EDGE_BORDER:
                    m = config.EDGE_MARGIN
                    cv2.rectangle(frame, (m, m), (w-m, h-m), config.DEBUG_COLOR_BORDER, 2)

                self.change_pixmap_signal.emit(frame)
            
            self.msleep(10)

        cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()