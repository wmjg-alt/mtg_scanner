from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QSizePolicy, QScrollArea, QHBoxLayout
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, Slot
import cv2
from gui.widgets import ActiveCardWidget
from PySide6.QtCore import Signal
from gui.widgets import ActiveCardWidget
from gui.ui_util import get_app_icon
import config

class MainWindow(QMainWindow):
    request_delete_signal = Signal(str) 
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MTG Scanner - Live Intake")
        self.setWindowIcon(get_app_icon()) # NEW
        self.resize(config.DEFAULT_WINDOW_WIDTH, config.DEFAULT_WINDOW_HEIGHT)
        self.setStyleSheet("background-color: #121212; color: white;")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # 1. Video
        self.video_label = QLabel("Initializing Camera...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: black; border: 1px solid #333;")
        self.video_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.main_layout.addWidget(self.video_label, stretch=2)

        # 2. Stats Bar (Updated)
        self.stats_label = QLabel("Objects Seen: 0 | Collection: 0 | Value: $0.00")
        self.stats_label.setStyleSheet("padding: 8px; font-weight: bold; background-color: #1e1e1e; border-top: 1px solid #333;")
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.stats_label)

        # 3. Active Cards Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        # Increase height to accommodate larger widgets (config + scrollbar buffer)
        self.scroll_area.setFixedHeight(config.WIDGET_HEIGHT + 40) 
        self.scroll_area.setStyleSheet("background-color: #1e1e1e; border: none;")
        
        self.cards_container = QWidget()
        self.cards_layout = QHBoxLayout(self.cards_container)
        
        # CENTER ALIGNMENT & SPACING
        self.cards_layout.setAlignment(Qt.AlignCenter) 
        self.cards_layout.setSpacing(20) # Nice gap between cards
        
        self.scroll_area.setWidget(self.cards_container)
        self.main_layout.addWidget(self.scroll_area)

        self.active_widgets = {} 
        self.seen_count = 0
        self.collection_count = 0
        self.total_value = 0.0

    @Slot(object)
    def update_image(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        if self.video_label.width() > 0:
            scaled = QPixmap.fromImage(qt_image).scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.video_label.setPixmap(scaled)

    @Slot(list)
    def update_tracked_objects(self, object_ids):
        current_ids = set(object_ids)
        existing_ids = set(self.active_widgets.keys())
        
        # Add new
        for tid in current_ids - existing_ids:
            widget = ActiveCardWidget(tid)
            widget.clicked.connect(self.handle_card_click)
            self.active_widgets[tid] = widget
            self.cards_layout.addWidget(widget)
            
        # Remove old
        for tid in existing_ids - current_ids:
            widget = self.active_widgets.pop(tid)
            self.cards_layout.removeWidget(widget)
            widget.deleteLater()

    @Slot(str, str, str, str, float)
    def update_card_info(self, tracker_id, name, price, path, conf):
        if tracker_id in self.active_widgets:
            self.active_widgets[tracker_id].update_data(name, price, path, conf)

    @Slot(str)
    def handle_card_click(self, tracker_id):
        if tracker_id in self.active_widgets:
            widget = self.active_widgets[tracker_id]
            widget.name_label.setText("RETRYING...")
            widget.image_label.clear()
        self.request_delete_signal.emit(tracker_id)

    @Slot(int)
    def update_seen_count(self, count):
        self.seen_count = count
        self._refresh_stats()

    @Slot(int, float)
    def update_collection_stats(self, count, val):
        self.collection_count = count
        self.total_value = val
        self._refresh_stats()

    def _refresh_stats(self):
        self.stats_label.setText(f"Objects Seen: {self.seen_count} | Collection: {self.collection_count} | Value: ${self.total_value:.2f}")