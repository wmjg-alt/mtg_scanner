import os
import cv2
import time
from PySide6.QtCore import QThread, Signal
from data.db_manager import DBManager
from services.mtg_service import MTGService
import config

class Librarian(QThread):
    # Signals now include more info for future GUI use
    card_found_signal = Signal(str, str, str) # Name, Price, LocalPath

    def __init__(self):
        super().__init__()
        self.db = DBManager()
        self.api = MTGService()
        self.queue = [] 
        self._run_flag = True

        os.makedirs(config.SCANS_DIR, exist_ok=True)

    def add_task(self, ocr_text, card_image):
        self.queue.append((ocr_text, card_image))

    def run(self):
        print("Librarian Service Started.")
        while self._run_flag:
            if self.queue:
                ocr_text, card_img = self.queue.pop(0)
                
                # 1. Check Alias Cache
                cached_resolution = self.db.get_alias(ocr_text)
                final_card_data = None
                
                if cached_resolution is False:
                    print(f"[Librarian] Skipping known invalid text: {ocr_text}")
                    continue
                elif cached_resolution:
                    print(f"[Librarian] Resolved '{ocr_text}' -> '{cached_resolution}' (Cache)")
                    final_card_data = self.db.get_catalog_card(cached_resolution)
                else:
                    # New Encounter
                    final_card_data = self.db.get_catalog_card(ocr_text)
                    if not final_card_data:
                        print(f"[Librarian] Unknown text '{ocr_text}'. Asking API...")
                        api_result = self.api.get_card_by_name(ocr_text)
                        
                        if api_result:
                            self.db.add_to_catalog(api_result)
                            real_name = api_result['name']
                            self.db.add_alias(ocr_text, real_name)
                            final_card_data = self.db.get_catalog_card(real_name)
                        else:
                            print(f"[Librarian] API failed. Marking '{ocr_text}' as Invalid.")
                            self.db.add_alias(ocr_text, None)

                # 2. Process Success
                if final_card_data:
                    final_name = final_card_data['display_name']
                    price = f"${final_card_data['price_usd']}" if final_card_data['price_usd'] else "N/A"
                    
                    # Archival
                    timestamp = int(time.time())
                    # Make filename safe
                    safe_name = "".join([c for c in final_name if c.isalnum()])
                    filename = f"{safe_name}_{timestamp}.jpg"
                    local_path = os.path.join(config.SCANS_DIR, filename)
                    
                    # Save Image
                    cv2.imwrite(local_path, card_img)
                    
                    # Log to Collection
                    self.db.log_scan(final_name, local_path)
                    
                    # Notify GUI
                    self.card_found_signal.emit(final_name, price, local_path)

            self.msleep(100)

    def stop(self):
        self._run_flag = False
        self.wait()