import cv2
from PySide6.QtCore import QThread, Signal
import numpy as np
from core.detector import CardDetector
import config

class VideoThread(QThread):
    change_pixmap_signal = Signal(np.ndarray)
    # New Signal: Sends a string of text to the GUI for debugging
    debug_info_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.detector = None 

    def run(self):
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
        # Request best resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.REQUEST_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.REQUEST_HEIGHT)

        if self.detector is None:
            self.detector = CardDetector()

        frame_count = 0
        last_boxes = [] 

        while self._run_flag:
            ret, frame = cap.read()
            if ret:
                # DYNAMIC RESOLUTION CHECK
                # We trust the frame itself.
                h, w = frame.shape[:2]
                
                frame_count += 1
                
                # --- DETECTION ---
                if frame_count % config.DETECT_EVERY_N_FRAMES == 0:
                    last_boxes = self.detector.detect(frame)
                    
                    # --- PREPARE DEBUG INFO ---
                    # Create a string summary: "Detected: cell phone (0.8), book (0.4)"
                    if last_boxes:
                        debug_texts = [f"{box[6]} ({box[4]:.2f})" for box in last_boxes]
                        debug_str = f"Resolution: {w}x{h} | Detections: " + ", ".join(debug_texts)
                    else:
                        debug_str = f"Resolution: {w}x{h} | Detections: None"
                    
                    self.debug_info_signal.emit(debug_str)

                # --- DRAWING ---
                if config.SHOW_DEBUG_BOXES:
                    for box in last_boxes:
                        # Unpack 7 items now
                        x1, y1, x2, y2, conf, cls, name = box
                        
                        cv2.rectangle(frame, (x1, y1), (x2, y2), config.DEBUG_COLOR_BOX, 4)
                        label = f"{name} {conf:.2f}" 
                        cv2.putText(frame, label, (x1, y1 - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, config.DEBUG_COLOR_BOX, 2)
                
                if config.SHOW_EDGE_BORDER:
                    m = config.EDGE_MARGIN
                    cv2.rectangle(frame, (m, m), (w-m, h-m), config.DEBUG_COLOR_BORDER, 2)

                self.change_pixmap_signal.emit(frame)
            
            self.msleep(10)

        cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()