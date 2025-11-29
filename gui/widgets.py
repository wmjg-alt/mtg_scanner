from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QCursor

class ActiveCardWidget(QFrame):
    clicked = Signal(str)

    def __init__(self, tracker_id):
        super().__init__()
        self.tracker_id = tracker_id
        
        self.setFixedSize(160, 260) # Taller for extra info
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setToolTip("Click to Delete / Retry")

        self.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 2px solid #555; 
                border-radius: 8px;
            }
            QFrame:hover {
                border: 2px solid #ff4444;
            }
            QLabel {
                color: white;
                border: none;
                background-color: transparent;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(4,4,4,4)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #000; border-radius: 4px;")
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.layout.addWidget(self.image_label, stretch=1)
        
        self.name_label = QLabel("Scanning...")
        self.name_label.setWordWrap(True)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.layout.addWidget(self.name_label)
        
        # Price Label
        self.price_label = QLabel("...")
        self.price_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.price_label)

        # Meta Label (ID + Conf)
        self.meta_label = QLabel(f"ID: {tracker_id}")
        self.meta_label.setAlignment(Qt.AlignCenter)
        self.meta_label.setStyleSheet("color: #777; font-size: 10px;")
        self.layout.addWidget(self.meta_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.tracker_id)
            
    def update_data(self, name, price_str, image_path, confidence):
        self.name_label.setText(name)
        
        # Price Logic
        price_color = "#aaaaaa" # Default Grey
        try:
            val = float(price_str.replace('$', ''))
            if val > 1.00:
                price_color = "#4fc3f7" # Blue
            elif val > 0.25:
                price_color = "#66bb6a" # Green
        except:
            pass # N/A stays grey
            
        self.price_label.setText(price_str)
        self.price_label.setStyleSheet(f"color: {price_color}; font-weight: bold; font-size: 14px;")
        
        # Meta Info
        self.meta_label.setText(f"ID: {self.tracker_id} | {confidence*100:.1f}%")
        
        # Image
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)