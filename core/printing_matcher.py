import cv2
import numpy as np
import os
import requests
import logging
import config

class PrintingMatcher:
    """
    Engine for identifying the specific printing (Set/Edition) of a card
    by comparing a local image against a list of Scryfall thumbnails.
    
    Uses two metrics:
    1. Structure: dHash (Difference Hash) 16x16.
    2. Color: HSV Histogram Correlation.
    """
    
    def __init__(self):
        self.cache_dir = config.THUMB_DIR
        os.makedirs(self.cache_dir, exist_ok=True)

    def _dhash(self, image, hash_size=16):
        """
        Calculate 16x16 Difference Hash.
        Returns a flattened boolean array (256 bits).
        """
        try:
            # 1. Grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # 2. Resize to (width+1, height)
            # We use 16x16 for higher fidelity than the standard 8x8
            resized = cv2.resize(gray, (hash_size + 1, hash_size))

            # 3. Compute gradients (True if col[x] > col[x+1])
            diff = resized[:, 1:] > resized[:, :-1]

            return diff.flatten()
        except Exception as e:
            logging.error(f"Hashing failed: {e}")
            return None

    def _color_hist_score(self, img1, img2):
        """
        Compare HSV color histograms.
        Returns correlation float: 1.0 (Identical) to 0.0 (Different).
        """
        #try:
        hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
        hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)

        # Calculate Hist for Hue (color) and Saturation (intensity)
        # Ignore Value (Brightness) to handle lighting differences
        hist1 = cv2.calcHist([hsv1], [0, 1], None, [30, 32], [0, 180, 0, 256])
        hist2 = cv2.calcHist([hsv2], [0, 1], None, [30, 32], [0, 180, 0, 256])

        cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
        cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)

        score = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        return max(0.0, score)
        # except:
        #     return 0.0

    def _download_thumb(self, url, card_id):
        """Lazy download of small thumbnails for matching"""
        if not url: return None
        
        # Use card_id to ensure uniqueness
        path = os.path.join(self.cache_dir, f"{card_id}_small.jpg")
        
        if os.path.exists(path):
            return cv2.imread(path)
            
        try:
            resp = requests.get(url, headers={"User-Agent": config.API_USER_AGENT})
            if resp.status_code == 200:
                with open(path, 'wb') as f:
                    f.write(resp.content)
                arr = np.frombuffer(resp.content, np.uint8)
                return cv2.imdecode(arr, cv2.IMREAD_COLOR)
        except Exception as e:
            logging.warning(f"Thumbnail download failed: {e}")
        return None

    def _get_year_delta(self, date_str):
        """Calculates year distance from user's preference"""
        try:
            year = int(date_str.split('-')[0])
            return abs(year - config.PREFERRED_SET_YEAR)
        except:
            return 999

    def find_best_match(self, user_scan, candidates):
        """
        Compares user_scan against a list of Scryfall candidates.
        """
        if not candidates: return None

        # 1. Compute Hash for User Scan (Check 0 and 180 rotations)
        # Scan might be upside down relative to Scryfall
        hash_0 = self._dhash(user_scan, 16)
        
        # We also rotate the scan 180 to check
        scan_180 = cv2.rotate(user_scan, cv2.ROTATE_180)
        hash_180 = self._dhash(scan_180, 16)

        scored = []
        logging.info(f"[Inspector] Matching {len(candidates)} prints...")

        for card in candidates:
            # Safety checks
            uris = card.get('image_uris')
            if not uris: continue # Some cards (Double Faced) handle uris differently, ignore for now
            
            thumb_url = uris.get('normal')
            ref_img = self._download_thumb(thumb_url, card['id'])
            if ref_img is None: continue

            # A. Structural Match (dHash)
            ref_hash = self._dhash(ref_img, 16)
            
            dist_0 = np.count_nonzero(hash_0 != ref_hash)
            dist_180 = np.count_nonzero(hash_180 != ref_hash)
            
            # Pick best orientation
            if dist_0 < dist_180:
                dist = dist_0
                scan_aligned = user_scan
            else:
                dist = dist_180
                scan_aligned = scan_180

            # B. Color Match (Histogram)
            # Only perform CPU-heavy color check if structure is plausible
            color_score = 0.0
            # if dist < 60: # 60 bits diff out of 256 is roughly 25% difference
            #     # Resize scan to match ref for fair histogram comparison
            h, w = ref_img.shape[:2]
            scan_resized = cv2.resize(scan_aligned, (w, h))
            color_score = self._color_hist_score(scan_resized, ref_img)

            # C. Era Preference
            year_delta = self._get_year_delta(card.get('released_at', '0000'))

            # D. Weighted Score
            # Structure (Dist) is dominant. Lower is better.
            # Color is secondary. Higher (0.0-1.0) is better.
            # We subtract color score * weight from distance to let color "heal" structure gaps.
            # Weight 25: A perfect color match (1.0) reduces distance score by 25.
            final_score = dist - (color_score * 25)

            scored.append({
                'card': card,
                'score': final_score,
                'dist': dist,
                'color': color_score,
                'year': year_delta,
                'set': card.get('set')
            })

        # Sort: 
        # 1. Final Weighted Score (Lower is better)
        # 2. Year Delta (Closest to 2015 wins ties)
        scored.sort(key=lambda x: (x['score'], x['year']))

        if not scored: return None
        
        winner = scored[0]
        
        # Logging top 3 for debugging
        for i, res in enumerate(scored[:3]):
            logging.info(f"   #{i+1} {res['set'].upper()}: Score {res['score']:.1f} (Dist {res['dist']} | Color {res['color']:.2f})")

        # Threshold check? 
        # Even if the best match is bad, we usually return it as the "best guess" 
        # but mark it if it's very weak.
        
        return winner['card']