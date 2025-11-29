import sys
import argparse
import logging
from PySide6.QtWidgets import QApplication

import config
from gui.window import MainWindow
from gui.dashboard import DashboardWindow
from core.video import VideoThread
from core.librarian import Librarian

logging.basicConfig(
    filename=config.LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'
)

def run_scanner():
    logging.info("Starting Scanner...")
    window = MainWindow()
    window.show()
    
    video = VideoThread()
    lib = Librarian()
    
    video.change_pixmap_signal.connect(window.update_image)
    video.tracker_ids_signal.connect(window.update_tracked_objects)
    video.scan_request_signal.connect(lib.add_task)
    video.objects_seen_signal.connect(window.update_seen_count)
    
    lib.card_found_signal.connect(window.update_card_info)
    lib.collection_stats_signal.connect(window.update_collection_stats)
    window.request_delete_signal.connect(lib.remove_entry)
    
    lib.start()
    video.start()
    
    app.aboutToQuit.connect(video.stop)
    app.aboutToQuit.connect(lib.stop)
    
    app.exec() # Blocks

def run_dashboard():
    logging.info("Starting Dashboard...")
    dash = DashboardWindow()
    dash.show()
    app.exec() # Blocks

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scanner-only", action="store_true")
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()

    app = QApplication(sys.argv)

    if args.report:
        run_dashboard()
    elif args.scanner_only:
        run_scanner()
    else:
        # Default: Scanner then Dashboard
        run_scanner()
        # Reset app instance for next run if needed, or just open next window
        # In PySide/Qt, app.exec() loops. When window closes, loop ends.
        # We can just start the next one.
        run_dashboard()