import os
import cv2
import time
import logging
from PySide6.QtCore import QThread, Signal
from data.db_manager import DBManager
from services.mtg_service import MTGService
from services.ocr_service import OCRService
import config


class Librarian(QThread):
    # Signals
    # ID, Name, Price, Path, Confidence
    card_found_signal = Signal(str, str, str, str, float) 
    # Count, Total Value
    collection_stats_signal = Signal(int, float) 

    def __init__(self):
        super().__init__()
        self.db = DBManager()
        self.api = MTGService()
        self.ocr = OCRService()
        self.queue = [] 
        self._run_flag = True
        self.active_scores = {} # ID -> Best Score (Len * Conf)
        os.makedirs(config.SCANS_DIR, exist_ok=True)

    def add_task(self, tracker_id, ocr_text, card_image):
        self.queue.append((tracker_id, ocr_text, card_image))

    def remove_entry(self, tracker_id):
        logging.info(f"[Librarian] Removing {tracker_id}")
        if tracker_id in self.active_scores:
            del self.active_scores[tracker_id]
        self.db.delete_scan(tracker_id)
        
        # Emit updated stats
        count, val = self.db.get_collection_summary()
        self.collection_stats_signal.emit(count, val)

    def run(self):
        logging.info("Librarian Service Started.")
        run_time = time.time()
        while self._run_flag:
            if self.queue:
                tracker_id, pre_text, card_img = self.queue.pop(0)
                
                best_img = card_img 
                ocr_text = pre_text
                current_score = 0
                current_conf = 0.0 # Track raw confidence for UI
                
                # --- STEP 1: OCR ---
                if not ocr_text:
                    ocr_text, conf, best_img = self.ocr.read_title(card_img)
                    current_conf = conf
                    current_score = len(ocr_text) * conf
                    if conf < 0.4: continue 
                else:
                    current_score = len(ocr_text) * 0.5
                    current_conf = 0.5

                # --- STEP 2: QUALITY GATE ---
                previous_best = self.active_scores.get(tracker_id, 0.0)
                if current_score <= previous_best:
                    continue

                # --- STEP 3: IDENTIFICATION ---
                final_card_data = None
                cached_resolution = self.db.get_alias(ocr_text)
                
                if cached_resolution is False: continue
                elif cached_resolution:
                    final_card_data = self.db.get_catalog_card(cached_resolution)
                else:
                    final_card_data = self.db.get_catalog_card(ocr_text)
                    if not final_card_data:
                        api_result = self.api.get_card_by_name(ocr_text)
                        if api_result:
                            self.db.add_to_catalog(api_result)
                            real_name = api_result['name']
                            self.db.add_alias(ocr_text, real_name)
                            final_card_data = self.db.get_catalog_card(real_name)
                        else:
                            self.db.add_alias(ocr_text, None)
                            continue

                # --- STEP 4: SAVE ---
                if final_card_data:
                    self.active_scores[tracker_id] = current_score
                    
                    final_name = final_card_data['display_name']
                    price_val = final_card_data['price_usd']
                    price_str = f"${price_val}" if price_val else "N/A"
                    
                    timestamp = int(time.time())
                    safe_name = "".join([c for c in final_name if c.isalnum()])
                    filename = f"{safe_name}_{timestamp}_{tracker_id}.jpg"
                    local_path = os.path.join(config.SCANS_DIR, filename)
                    cv2.imwrite(local_path, best_img)
                    
                    self.db.update_scan(tracker_id, final_name, local_path)
                    
                    # Update GUI with Confidence
                    self.card_found_signal.emit(tracker_id, final_name, price_str, local_path, current_conf)
                    
                    # Update Stats
                    count, total_val = self.db.get_collection_summary()
                    self.collection_stats_signal.emit(count, total_val)
                elapsed = time.time() - run_time
                logging.info(f"[Librarian] Processed {tracker_id} in {elapsed:.2f}s")
            self.msleep(100)

    def stop(self):
        self._run_flag = False
        self.wait()