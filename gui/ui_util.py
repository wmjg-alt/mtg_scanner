import os
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QPen
from PySide6.QtCore import Qt

def get_app_icon():
    """
    Returns a QIcon. 
    Prioritizes 'assets/icon.png' if it exists.
    Otherwise generates a procedural MTG-themed icon.
    """
    # 1. Check for file
    icon_path = os.path.join("assets", "icon.png")
    if os.path.exists(icon_path):
        return QIcon(icon_path)

    # 2. Generate Procedural Icon (Purple/Black Card Back theme)
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Background (Dark Rect)
    painter.setBrush(QColor("#1e1e1e"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(4, 4, size-8, size-8, 8, 8)
    
    # Border (Purple)
    pen = QPen(QColor("#9c27b0"))
    pen.setWidth(4)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    painter.drawRoundedRect(4, 4, size-8, size-8, 8, 8)
    
    # Center Symbol (Circle)
    painter.setBrush(QColor("#9c27b0"))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(20, 20, 24, 24)
    
    painter.end()
    
    return QIcon(pixmap)