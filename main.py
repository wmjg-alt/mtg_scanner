import sys
from PySide6.QtWidgets import QApplication
from gui.window import MainWindow
from core.video import VideoThread

def main():
    app = QApplication(sys.argv)
    
    # 1. Setup UI
    window = MainWindow()
    window.show()
    
    # 2. Setup Camera Thread
    # Note: If you have multiple cameras, change index 0 to 1
    thread = VideoThread(camera_index=0)
    
    # 3. Connect Signals
    # When the thread gets a new frame, send it to the window
    thread.change_pixmap_signal.connect(window.update_image)
    
    # 4. Start Thread
    thread.start()
    
    # 5. Handle Exit
    # We need to make sure the thread stops when we close the window
    app.aboutToQuit.connect(thread.stop)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()