import cv2
import os
import glob
import numpy as np
from core.image_processor import ImageProcessor
from services.ocr_service import OCRService
from random import choice

def get_ground_truth_sample_hd():
    """
    1. Finds a label in the VALIDATION dataset.
    2. Calculates the High-Res coordinates.
    3. Loads the matching ORIGINAL 4K image.
    """
    # 1. Look for labels
    base_path = os.path.join("dataset", "formatted", "valid")
    label_dir = os.path.join(base_path, "labels")
    
    # Grab the first label file
    label_files = glob.glob(os.path.join(label_dir, "*.txt"))
    if not label_files:
        print(f"No labels found in {label_dir}")
        return None, None
        
    # pick randomly from label_files
    r = choice(range(len(label_files)))
    target_label_path = label_files[r]
    print(r, target_label_path)
    label_filename = os.path.basename(target_label_path)
    
    # 2. Derive the Original Raw Filename
    # Roboflow format: mtg_data_0002_jpg.rf.24ec....txt
    # We want: mtg_data_0002.jpg
    
    # Split by the "_jpg" tag usually added by Roboflow
    if "_jpg" in label_filename:
        raw_name = label_filename.split("_jpg")[0] + ".jpg"
    else:
        # Fallback if naming is different
        raw_name = label_filename.split(".")[0] + ".jpg"
        
    raw_img_path = os.path.join("dataset", "raw_images", raw_name)
    
    if not os.path.exists(raw_img_path):
        print(f"Could not find original raw image: {raw_img_path}")
        print("Did you delete the raw_images folder?")
        return None, None
        
    print(f"Testing Label: {label_filename}")
    print(f"Using HD Image: {raw_name}")
    
    # 3. Read HD Image
    img = cv2.imread(raw_img_path)
    if img is None:
        print("Failed to load image.")
        return None, None
        
    h_img, w_img = img.shape[:2]
    print(f"Resolution: {w_img}x{h_img}")
    
    # 4. Parse YOLO Label & Scale to 4K
    with open(target_label_path, 'r') as f:
        line = f.readline().strip()
        if not line: return None, None
        parts = line.split()
        
        c_x = float(parts[1])
        c_y = float(parts[2])
        w_norm = float(parts[3])
        h_norm = float(parts[4])
        
        # Convert to Pixel Coordinates (Using HD dims)
        pixel_w = w_norm * w_img
        pixel_h = h_norm * h_img
        pixel_cx = c_x * w_img
        pixel_cy = c_y * h_img
        
        x1 = int(pixel_cx - (pixel_w / 2))
        y1 = int(pixel_cy - (pixel_h / 2))
        x2 = int(pixel_cx + (pixel_w / 2))
        y2 = int(pixel_cy + (pixel_h / 2))
        
        return img, [x1, y1, x2, y2]

def test():
    processor = ImageProcessor()
    ocr = OCRService()
    
    # 1. Get Clean Data (HD)
    frame, box = get_ground_truth_sample_hd()
    if frame is None:
        return

    # Visual check of input
    # Resize for display because 4K is too big for screen
    debug_input = cv2.resize(frame, (1280, 720)) 

    
    cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)
    cv2.imshow("1. HD Input (Resized for View)", debug_input)

    # 2. Warping (On the full 4K image)
    print("Attempting to Warp...")
    try:
        card_img = processor.process_card(frame, box)
    except Exception as e:
        print(f"Warping Failed: {e}")
        return

    # 3. OCR
    print("Attempting OCR...")
    # This usually takes 0.5s - 1.0s on CPU
    text, conf, _img = ocr.read_title(card_img)
    cv2.imshow("2. Warped Result", _img)

    print(f"\n--- RESULTS ---")
    print(f"Text: '{text}'")
    print(f"Conf: {conf:.2f}")
    
    print("\nPress any key on the image windows to exit.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test()