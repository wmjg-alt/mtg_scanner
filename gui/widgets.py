from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QCursor
import config

class ActiveCardWidget(QFrame):
    clicked = Signal(str)

    def __init__(self, tracker_id):
        super().__init__()
        self.tracker_id = tracker_id
        
        # Responsive sizing from config
        self.setFixedSize(config.WIDGET_WIDTH, config.WIDGET_HEIGHT)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setToolTip("Click to Delete / Retry")

        self.setStyleSheet("""
            QFrame {
                background-color: #252525;
                border: 2px solid #444; 
                border-radius: 12px;
            }
            QFrame:hover {
                border: 2px solid #ff4444;
                background-color: #2a2a2a;
            }
            QLabel {
                color: #e0e0e0;
                border: none;
                background-color: transparent;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(4)
        
        # Image Area
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #000; border-radius: 6px;")
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.layout.addWidget(self.image_label, stretch=1)
        
        # Name
        self.name_label = QLabel("Scanning...")
        self.name_label.setWordWrap(True)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 4px;")
        self.layout.addWidget(self.name_label)
        
        # Price
        self.price_label = QLabel("...")
        self.price_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.price_label)

        # Meta (ID + Conf)
        self.meta_label = QLabel(f"ID: {tracker_id}")
        self.meta_label.setAlignment(Qt.AlignCenter)
        self.meta_label.setStyleSheet("color: #666; font-size: 10px; font-family: monospace;")
        self.layout.addWidget(self.meta_label)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.tracker_id)
            
    def update_data(self, name, price_str, image_path, confidence):
        self.name_label.setText(name)
        
        # Price Logic
        price_val = 0.0
        try:
            # Clean string "$1,200.50" -> 1200.50
            price_val = float(price_str.replace('$', '').replace(',', ''))
        except:
            pass

        # Determine Color based on Config
        # We default to bulk
        final_color = config.PRICE_ALERTS["bulk"]["color"]
        
        # Check high to low logic
        if price_val >= config.PRICE_ALERTS["mythic"]["min"]:
            final_color = config.PRICE_ALERTS["mythic"]["color"]
        elif price_val >= config.PRICE_ALERTS["rare"]["min"]:
            final_color = config.PRICE_ALERTS["rare"]["color"]
        elif price_val >= config.PRICE_ALERTS["uncommon"]["min"]:
            final_color = config.PRICE_ALERTS["uncommon"]["color"]
        elif price_val >= config.PRICE_ALERTS["common"]["min"]:
            final_color = config.PRICE_ALERTS["common"]["color"]
            
        self.price_label.setText(price_str)
        self.price_label.setStyleSheet(f"color: {final_color}; font-weight: 800; font-size: 18px;")
        
        # Meta Info (3 decimal places)
        self.meta_label.setText(f"ID: {self.tracker_id} | Conf: {confidence:.3f}")
        
        # Image
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            # Scale to fit the label's current size
            scaled = pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)