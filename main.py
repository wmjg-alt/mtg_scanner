import sys
from PySide6.QtWidgets import QApplication
from gui.window import MainWindow
from core.video import VideoThread

def main():
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    thread = VideoThread()
    
    # Connect Image Signal
    thread.change_pixmap_signal.connect(window.update_image)
    
    # Connect Debug Text Signal (NEW)
    thread.debug_info_signal.connect(window.update_debug_text)
    
    thread.start()
    app.aboutToQuit.connect(thread.stop)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()