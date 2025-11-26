import easyocr
import cv2
import numpy as np

class OCRService:
    def __init__(self):
        print("Initializing OCR Engine...")
        self.reader = easyocr.Reader(['en'], gpu=True) 

    def _get_text_from_crop(self, crop):
        result = self.reader.readtext(crop, detail=1)
        if not result: return "", 0.0
        
        valid_results = [res for res in result if res[2] > 0.3]
        if not valid_results: return "", 0.0
            
        text = " ".join([res[1] for res in valid_results])
        avg_conf = sum([res[2] for res in valid_results]) / len(valid_results)
        return text, avg_conf

    def calculate_score(self, txt, conf):
        alpha_count = sum(c.isalpha() for c in txt) # 1-15 likely
        # combine alpha count and confidence for scoring, weighted out of 1
        score = (alpha_count / 15.0) * 0.6 + (conf) * 0.4
        return score

    def read_title(self, card_image):
        """
        Returns: (text, confidence, upright_image)
        """
        h, w = card_image.shape[:2]
        candidates = []

        if h > w:
            # PORTRAIT: Test Upright vs 180
            crop_h = int(h * 0.15)
            
            # 1. Upright
            crop_up = card_image[0:crop_h, 0:w]
            txt, conf = self._get_text_from_crop(crop_up)
            candidates.append((txt, conf, card_image)) # Return original

            # 2. Upside Down
            img_rot = cv2.rotate(card_image, cv2.ROTATE_180)
            crop_rot = img_rot[0:crop_h, 0:w]
            txt, conf = self._get_text_from_crop(crop_rot)
            candidates.append((txt, conf, img_rot)) # Return rotated

        else:
            # LANDSCAPE: Test 90 CW vs 90 CCW
            # 1. CW
            img_cw = cv2.rotate(card_image, cv2.ROTATE_90_CLOCKWISE)
            h_new, w_new = img_cw.shape[:2]
            crop_h = int(h_new * 0.15)
            crop_cw = img_cw[0:crop_h, 0:w_new]
            txt, conf = self._get_text_from_crop(crop_cw)
            candidates.append((txt, conf, img_cw))

            # 2. CCW
            img_ccw = cv2.rotate(card_image, cv2.ROTATE_90_COUNTERCLOCKWISE)
            crop_ccw = img_ccw[0:crop_h, 0:w_new]
            txt, conf = self._get_text_from_crop(crop_ccw)
            candidates.append((txt, conf, img_ccw))

        # Scoring
        best_txt = ""
        best_conf = 0.0
        max_score = -1
        best_img = card_image # Default

        for txt, conf, img in candidates:
            print(txt, conf)
            score = self.calculate_score(txt, conf)
            if score > max_score:
                max_score = score
                best_txt = txt
                best_conf = conf
                best_img = img

        return best_txt, best_conf, best_img