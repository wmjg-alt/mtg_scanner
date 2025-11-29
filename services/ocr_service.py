import easyocr
import cv2
import numpy as np
import time
import logging
import os
import config

class OCRService:
    def __init__(self):
        logging.info("Initializing EasyOCR Engine (GPU)...")
        # Load model into memory once.
        self.reader = easyocr.Reader(['en'], gpu=True) 

    def _enhance_image(self, crop):
        """
        Enhance text visibility:
        1. Resize 2x (Helps OCR read small fonts)
        2. Grayscale
        3. CLAHE (Contrast Enhancement for white text on light backgrounds)
        """
        # 1. Upscale
        h, w = crop.shape[:2]
        scaled = cv2.resize(crop, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
        
        # 2. Grayscale
        gray = cv2.cvtColor(scaled, cv2.COLOR_BGR2GRAY)
        
        # 3. CLAHE (Contrast Limited Adaptive Histogram Equalization)
        # This is better than global thresholding for textured cards
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        return enhanced

    def _get_text_from_crop(self, crop, tag=""):
        """Runs OCR on a specific image slice"""
        start = time.time()
        
        # Preprocess the crop for the AI (Grayscale/Contrast)
        # BUT we don't return this ugly image. We just use it for reading.
        ai_input = self._enhance_image(crop)
        
        # detail=1 gives coords, text, confidence
        try:
            result = self.reader.readtext(ai_input, detail=1)
        except Exception as e:
            logging.error(f"[OCR] Error in readtext: {e}")
            return "", 0.0

        elapsed = time.time() - start
        
        if not result:
            return "", 0.0
        
        # Filter garbage
        valid_results = [res for res in result if res[2] > 0.3]
        
        if not valid_results:
            return "", 0.0
            
        text = " ".join([res[1] for res in valid_results])
        avg_conf = sum([res[2] for res in valid_results]) / len(valid_results)
        
        if elapsed > 0.2:
            logging.info(f"[OCR] {tag:<10} | Time: {elapsed:.2f}s | Conf: {avg_conf:.2f} | Text: '{text}'")
        
        return text, avg_conf

    def calculate_score(self, txt, conf):
        # Smart scoring: weighting confidence and text length separately, out of 1
        alpha_count = sum(c.isalpha() for c in txt)
        score = (alpha_count / 30.0) * 0.6 + (conf) * 0.4
        return score

    def read_title(self, card_image):
        """
        Input: Flattened Color Card Image.
        Output: (text, confidence, CORRECTED_COLOR_IMAGE)
        """
        start_total = time.time()
        h, w = card_image.shape[:2]
        
        # Decide orientations based on aspect ratio
        candidates = []

        if h > w:
            # PORTRAIT: Upright vs 180
            # 1. Upright
            crop_h = int(h * config.CROP_TITLE_RATIO)
            crop_up = card_image[0:crop_h, 0:w]
            txt, conf = self._get_text_from_crop(crop_up, "Upright")
            candidates.append((txt, conf, card_image))

            # Early Exit: If great result, stop.
            if conf > 0.8 and len(txt) > 4:
                logging.info(f"[OCR] Early Exit (Upright). Total: {time.time()-start_total:.2f}s")
                return txt, conf, card_image

            # 2. Upside Down
            img_rot = cv2.rotate(card_image, cv2.ROTATE_180)
            crop_rot = img_rot[0:crop_h, 0:w]
            txt, conf = self._get_text_from_crop(crop_rot, "Inverted")
            candidates.append((txt, conf, img_rot))

        else:
            # LANDSCAPE: 90 CW vs 90 CCW
            # 1. CW
            img_cw = cv2.rotate(card_image, cv2.ROTATE_90_CLOCKWISE)
            h_new, w_new = img_cw.shape[:2]
            crop_h = int(h_new * config.CROP_TITLE_RATIO)
            crop_cw = img_cw[0:crop_h, 0:w_new]
            txt, conf = self._get_text_from_crop(crop_cw, "Rot-CW")
            candidates.append((txt, conf, img_cw))

            # 2. CCW
            img_ccw = cv2.rotate(card_image, cv2.ROTATE_90_COUNTERCLOCKWISE)
            crop_ccw = img_ccw[0:crop_h, 0:w_new]
            txt, conf = self._get_text_from_crop(crop_ccw, "Rot-CCW")
            candidates.append((txt, conf, img_ccw))

        # Scoring
        best_txt = ""
        best_conf = 0.0
        max_score = -1
        best_img = card_image # Default to original if fail

        for txt, conf, img in candidates:
            score = self.calculate_score(txt, conf)

            if score > max_score:
                max_score = score
                best_txt = txt
                best_conf = conf
                best_img = img # IMPORTANT: This is the COLOR image, rotated correctly

        logging.info(f"[OCR] Winner: '{best_txt}' (Score {max_score:.1f}). Total: {time.time()-start_total:.2f}s")

        return best_txt, best_conf, best_img