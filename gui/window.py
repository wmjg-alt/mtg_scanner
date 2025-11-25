from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QSizePolicy
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, Slot
import cv2

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MTG Scanner - Phase 2.5 (Debug)")
        self.resize(1000, 800) 

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Video
        self.video_label = QLabel("Initializing Camera...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: #222; color: #AAA;")
        self.video_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.layout.addWidget(self.video_label, stretch=1) # stretch=1 takes all available space

        # DEBUG LABEL
        self.debug_label = QLabel("Waiting for detection...")
        self.debug_label.setAlignment(Qt.AlignCenter)
        self.debug_label.setStyleSheet("background-color: #333; color: #00FF00; font-family: monospace; padding: 5px;")
        self.debug_label.setFixedHeight(40) # Keep it small at the bottom
        self.layout.addWidget(self.debug_label)

    @Slot(object)
    def update_image(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        if self.video_label.width() > 0 and self.video_label.height() > 0:
            scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
                self.video_label.width(), 
                self.video_label.height(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.video_label.setPixmap(scaled_pixmap)

    @Slot(str)
    def update_debug_text(self, text):
        """Updates the label below the video"""
        self.debug_label.setText(text)