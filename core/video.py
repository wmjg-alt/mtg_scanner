import cv2
import time
from PySide6.QtCore import QThread, Signal
import numpy as np
from core.detector import CardDetector
from core.tracker import CentroidTracker
from core.image_processor import ImageProcessor
import config

class VideoThread(QThread):
    # Signal to update the main video display
    change_pixmap_signal = Signal(np.ndarray)
    # Signal to tell the GUI which Cards are currently active (for Widgets)
    tracker_ids_signal = Signal(list)
    # Signal to ask Librarian to identify a card: (TrackerID, EmptyText, WarpedImage)
    scan_request_signal = Signal(str, str, np.ndarray)
    # Signal for debug text overlay
    debug_info_signal = Signal(str)
    # Objects Seen Signal
    objects_seen_signal = Signal(int)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.detector = None 
        self.tracker = CentroidTracker() 
        self.image_processor = ImageProcessor()

    def run(self):
        # Initialize Camera
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.REQUEST_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.REQUEST_HEIGHT)

        # Initialize Detector (Lazy Load)
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
                confidences = [] 
                
                # Run YOLO every N frames
                if frame_count % config.DETECT_EVERY_N_FRAMES == 0:
                    detections = self.detector.detect(frame)
                    for item in detections:
                        # item = [x1, y1, x2, y2, conf, cls, name]
                        rects.append(item[0:4]) 
                        confidences.append(item[4])
                    
                    # Update Tracker
                    objects = self.tracker.update(rects)
                else:
                    objects = self.tracker.objects

                # --- 2. GUI SYNC & SCANNING LOGIC ---
                active_ids = list(objects.keys())
                
                # Notify GUI about active objects (to create/delete widgets)
                self.tracker_ids_signal.emit(active_ids)
                
                # EMIT STATS
                # We can grab total seen from the tracker's stats manager
                total_seen = self.tracker.stats.stats.get("total_objects_seen", 0)
                self.objects_seen_signal.emit(total_seen)
                
                # Trigger Scan periodically (Every 30 frames = ~1 second)
                if frame_count % 30 == 0:
                    for objectID in active_ids:
                        if objectID in self.tracker.bboxes:
                            box = self.tracker.bboxes[objectID]
                            # Warp the card to flat view
                            warped_img = self.image_processor.process_card(frame, box)
                            # Send to Librarian (Empty text = "Please read this")
                            self.scan_request_signal.emit(objectID, "", warped_img)

                # --- 3. DEBUG VISUALIZATION ---
                # Build debug string
                if objects:
                    # We don't have exact confidence for tracked objects easily accessible 
                    # between frames, so we just show count/IDs
                    debug_str = f"Tracking {len(objects)} Cards | IDs: {active_ids}"
                else:
                    debug_str = "Tracking: None"
                self.debug_info_signal.emit(debug_str)

                # Draw Visuals
                for (objectID, centroid) in objects.items():
                    if objectID in self.tracker.bboxes:
                        box = self.tracker.bboxes[objectID]
                        (x1, y1, x2, y2) = box
                        
                        if config.SHOW_DEBUG_BOXES:
                            # Green Box
                            cv2.rectangle(frame, (x1, y1), (x2, y2), config.DEBUG_COLOR_BOX, 2)
                            
                            # Red ID Text
                            text = f"ID {objectID}"
                            cv2.putText(frame, text, (centroid[0] - 10, centroid[1] - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                            
                            # Red Centroid Dot
                            cv2.circle(frame, (centroid[0], centroid[1]), 4, (0, 0, 255), -1)

                            # Yellow Search Radius
                            cv2.circle(frame, (centroid[0], centroid[1]), 
                                       config.MAX_TRACKING_DISTANCE, (0, 255, 255), 1)

                        # Draw Trails
                        if objectID in self.tracker.history:
                            history = self.tracker.history[objectID]
                            for i in range(1, len(history)):
                                if history[i - 1] is None or history[i] is None: continue
                                cv2.line(frame, history[i - 1], history[i], (0, 0, 255), 2)

                # Draw Safety Border
                if config.SHOW_EDGE_BORDER:
                    m = config.EDGE_MARGIN
                    cv2.rectangle(frame, (m, m), (w-m, h-m), config.DEBUG_COLOR_BORDER, 2)

                self.change_pixmap_signal.emit(frame)
            
            self.msleep(10)

        cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()