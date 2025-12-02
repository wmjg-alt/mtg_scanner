import cv2
import logging
import time
from PySide6.QtCore import QThread, Signal
from data.db_manager import DBManager
from services.mtg_service import MTGService
from core.printing_matcher import PrintingMatcher

class Inspector(QThread):
    # Signal: (TrackerID, NewSetCode, NewPrice)
    inspection_complete_signal = Signal(str, str, str)
    # Signal: (TrackerID, StatusMessage) - For UI feedback like "Downloading..."
    status_signal = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.db = DBManager()
        self.api = MTGService()
        self.matcher = PrintingMatcher()
        self.queue = [] # List of (tracker_id, card_name, image_path)
        self._run_flag = True

    def add_task(self, tracker_id, card_name, image_path):
        """Queue a card for visual verification"""
        self.queue.append((tracker_id, card_name, image_path))

    def run(self):
        logging.info("Inspector Service Started.")
        while self._run_flag:
            if self.queue:
                tracker_id, name, img_path = self.queue.pop(0)
                logging.info(f"[Inspector] Analyzing {name} ({tracker_id})...")
                self.status_signal.emit(tracker_id, "Fetching prints...")

                # 1. Load Local Scan
                user_scan = cv2.imread(img_path)
                if user_scan is None:
                    logging.error(f"[Inspector] Could not load image: {img_path}")
                    self.status_signal.emit(tracker_id, "Error loading image")
                    continue

                # 2. Fetch Candidates
                candidates = self.api.search_all_printings(name)
                if not candidates:
                    self.status_signal.emit(tracker_id, "No prints found")
                    continue

                # 3. Visual Match
                self.status_signal.emit(tracker_id, f"Comparing {len(candidates)} versions...")
                
                # This performs the dHash + Color Histogram logic
                best_match = self.matcher.find_best_match(user_scan, candidates)

                # 4. Save Result
                if best_match:
                    set_code = best_match.get('set', '???').upper()
                    price = best_match.get('prices', {}).get('usd', 'N/A')
                    logging.info(f"[Inspector] Match confirmed: {set_code}")
                    
                    # Update the Catalog with the SPECIFIC printing details
                    # (Note: Currently overwrites the default entry for this card name)
                    self.db.add_to_catalog(best_match)
                    
                    # Notify UI
                    self.inspection_complete_signal.emit(tracker_id, set_code, str(price))
                else:
                    self.status_signal.emit(tracker_id, "Match failed")

            self.msleep(100)

    def stop(self):
        self._run_flag = False
        self.wait()