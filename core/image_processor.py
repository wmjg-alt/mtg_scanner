import cv2
import numpy as np
import scipy.spatial.distance as dist

class ImageProcessor:
    def __init__(self):
        # Base dimensions
        self.std_w = 630
        self.std_h = 880

    def order_points(self, pts):
        # Sort points: TL, TR, BR, BL
        xSorted = pts[np.argsort(pts[:, 0]), :]
        leftMost = xSorted[:2, :]
        rightMost = xSorted[2:, :]
        leftMost = leftMost[np.argsort(leftMost[:, 1]), :]
        (tl, bl) = leftMost
        D = dist.cdist(tl[np.newaxis], rightMost, "euclidean")[0]
        (br, tr) = rightMost[np.argsort(D)[::-1], :]
        return np.array([tl, tr, br, bl], dtype="float32")

    def process_card(self, frame, box):
        x1, y1, x2, y2 = box
        
        # Add Padding
        h_img, w_img = frame.shape[:2]
        pad = 20
        x1 = max(0, x1 - pad)
        y1 = max(0, y1 - pad)
        x2 = min(w_img, x2 + pad)
        y2 = min(h_img, y2 + pad)

        crop = frame[y1:y2, x1:x2]
        
        # Find Contours
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blur, 75, 200)
        
        cnts, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]
        
        displayCnt = None
        for c in cnts:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4:
                displayCnt = approx
                break

        if displayCnt is not None:
            pts = displayCnt.reshape(4, 2)
            rect = self.order_points(pts)
            
            # --- NEW ASPECT RATIO LOGIC ---
            (tl, tr, br, bl) = rect
            
            # Calculate width and height of the detected polygon
            widthA = np.linalg.norm(br - bl)
            widthB = np.linalg.norm(tr - tl)
            maxWidth = max(int(widthA), int(widthB))

            heightA = np.linalg.norm(tr - br)
            heightB = np.linalg.norm(tl - bl)
            maxHeight = max(int(heightA), int(heightB))

            # Decide orientation based on physical pixels found
            if maxWidth > maxHeight:
                # Landscape (Sideways card)
                dst_w, dst_h = self.std_h, self.std_w # 880, 630
            else:
                # Portrait (Upright card)
                dst_w, dst_h = self.std_w, self.std_h # 630, 880

            dst = np.array([
                [0, 0],
                [dst_w - 1, 0],
                [dst_w - 1, dst_h - 1],
                [0, dst_h - 1]], dtype="float32")

            M = cv2.getPerspectiveTransform(rect, dst)
            warped = cv2.warpPerspective(crop, M, (dst_w, dst_h))
            return warped
        else:
            # Fallback: maintain aspect ratio of the bounding box
            box_w = x2 - x1
            box_h = y2 - y1
            if box_w > box_h:
                 return cv2.resize(crop, (self.std_h, self.std_w))
            else:
                 return cv2.resize(crop, (self.std_w, self.std_h))