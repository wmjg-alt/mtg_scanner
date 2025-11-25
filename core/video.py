import cv2
import sys
from PySide6.QtCore import QThread, Signal
import numpy as np

class VideoThread(QThread):
    # We emit a numpy array (the image frame) to the GUI
    change_pixmap_signal = Signal(np.ndarray)

    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self._run_flag = True

    def run(self):
        # Initialize the webcam
        cap = cv2.VideoCapture(self.camera_index)
        
        # Request 4K resolution (3840x2160)
        # Even if the camera doesn't support 4K, OpenCV will default to the max available.
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)
        
        while self._run_flag:
            ret, frame = cap.read()
            if ret:
                # Emit the frame to the GUI thread
                self.change_pixmap_signal.emit(frame)
            
            # This sleep isn't strictly necessary for CV2, 
            # but it prevents this thread from hogging 100% of a CPU core.
            self.msleep(10)

        # Cleanup
        cap.release()

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()