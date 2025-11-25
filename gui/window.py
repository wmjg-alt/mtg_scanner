from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QSizePolicy
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, Slot
import cv2

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MTG Scanner - Phase 1 (Scalable)")
        
        # We set a small default size, but allow it to go even smaller
        self.resize(800, 600) 

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        # Remove margins so the video can touch the edges if desired
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.video_label = QLabel("Initializing Camera...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: #222; color: #AAA;")
        
        # --- THE FIX ---
        # QSizePolicy.Ignored tells the layout: 
        # "I don't care how big the image inside me is, shrink me as much as you want."
        self.video_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        
        self.layout.addWidget(self.video_label)

    @Slot(object)
    def update_image(self, cv_img):
        """Updates the video_label with a new opencv image"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Safety check: Don't try to scale if the window is collapsed (width=0)
        if self.video_label.width() > 0 and self.video_label.height() > 0:
            # Scale to the current size of the label (which is determined by the window size)
            scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                self.video_label.width(), 
                self.video_label.height(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.video_label.setPixmap(scaled_pixmap)