import sys
import os
import time
import importlib
import logging

# Load Project Config
try:
    import config
except ImportError:
    print("CRITICAL: config.py not found.")
    sys.exit(1)

# Color Codes for Console
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def print_status(component, status, message=""):
    color = GREEN if status == "OK" else RED
    if status == "WARN": color = YELLOW
    print(f"[{component:<15}] {color}{status:<6}{RESET} {message}")

def check_dependencies():
    print("\n--- 1. DEPENDENCY CHECK ---")
    required = []
    with open("requirements.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("-"):
                pkg = line.split("==")[0].split(">=")[0].split("<=")[0]
                if pkg == "opencv-python":
                    required.append("cv2")
                else:
                    required.append(pkg)
    
    all_good = True
    for lib in required:
        try:
            importlib.import_module(lib)
            print_status(lib, "OK")
        except ImportError:
            print_status(lib, "FAIL", "Not installed")
            all_good = False
    return all_good

def check_hardware():
    print("\n--- 2. HARDWARE CHECK ---")
    
    # Torch/CUDA
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print_status("CUDA", "OK", f"GPU: {gpu_name}")
        else:
            print_status("CUDA", "WARN", "Running on CPU (Slow)")
    except Exception as e:
        print_status("CUDA", "FAIL", f"Torch error: {e}")

    # EasyOCR
    try:
        import easyocr
        # Just check import
        print_status("EasyOCR", "OK", "Library ready")
    except:
        print_status("EasyOCR", "FAIL")

    import cv2
    try:
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
        
        if not cap.isOpened():
            print_status("Camera", "FAIL", f"Index {config.CAMERA_INDEX} not found")
        else:
            # FORCE Request the Config Resolution (just like the real app)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.REQUEST_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.REQUEST_HEIGHT)
            
            ret, frame = cap.read()
            if ret:
                h, w = frame.shape[:2]
                
                # Check if we got what we asked for (allow small variance for aspect ratios)
                status = "OK"
                if w < config.REQUEST_WIDTH * 0.9:
                    status = "WARN"
                    msg = f"Got {w}x{h} (Requested {config.REQUEST_WIDTH}x{config.REQUEST_HEIGHT})"
                else:
                    msg = f"Resolution: {w}x{h} (Confirmed)"
                    
                print_status("Camera", status, msg)
            else:
                print_status("Camera", "WARN", "Connected but failed to grab frame (Privacy shutter?)")
            
            cap.release()
    except Exception as e:
        print_status("Camera", "FAIL", str(e))

def check_filesystem():
    print("\n--- 3. FILESYSTEM CHECK ---")
    
    # Models
    if os.path.exists(config.MODEL_PATH):
        print_status("YOLO Model", "OK", f"Found at {config.MODEL_PATH}")
    else:
        print_status("YOLO Model", "FAIL", "Missing best.pt")

    # DB
    if os.path.exists(config.DB_PATH):
        print_status("Database", "OK", "Found")
    else:
        print_status("Database", "WARN", "Not found (Will be created on run)")

    # Scans
    if os.path.exists(config.SCANS_DIR):
        print_status("Scans Dir", "OK", "Found")
    else:
        try:
            os.makedirs(config.SCANS_DIR, exist_ok=True)
            print_status("Scans Dir", "OK", "Created")
        except Exception as e:
            print_status("Scans Dir", "FAIL", str(e))

def check_api():
    print("\n--- 4. API CONNECTION ---")
    import requests
    
    # Use Config Headers to simulate real app behavior
    headers = {
        "User-Agent": config.API_USER_AGENT,
        "Accept": "*/*"
    }
    
    try:
        start = time.time()
        # We ping the root API endpoint which returns status JSON
        # This is polite and lightweight. /cards/named?fuzzy=aust+com 
        resp = requests.get(config.API_BASE_URL + "/cards/named?fuzzy=aust+com",
                            headers=headers, 
                            timeout=5)
        ping = (time.time() - start) * 1000
        
        if resp.status_code == 200:
            print_status("Scryfall", "OK", f"Ping: {ping:.0f}ms (Headers Validated)")
        else:
            print_status("Scryfall", "FAIL", f"Status Code: {resp.status_code} ")
    except Exception as e:
        print_status("Scryfall", "FAIL", str(e))

def check_logic():
    print("\n--- 5. LOGIC SMOKE TEST ---")
    # Silence logger for these imports
    logging.disable(logging.CRITICAL)
    
    try:
        from core.image_processor import ImageProcessor
        ip = ImageProcessor()
        print_status("ImageProc", "OK", "Initialized")
    except Exception as e:
        print_status("ImageProc", "FAIL", str(e))

    try:
        from data.db_manager import DBManager
        db = DBManager()
        # Just check if we can read stats without crashing
        stats = db.get_dashboard_stats()
        print_status("DB Logic", "OK", f"Cards in collection: {stats['total_count']}")
    except Exception as e:
        print_status("DB Logic", "FAIL", str(e))
        
    logging.disable(logging.NOTSET) # Restore logging

if __name__ == "__main__":
    print(f"MTG Scanner Diagnostic Tool")
    print(f"===========================")
    
    check_dependencies()
    check_filesystem()
    check_hardware()
    check_api()
    check_logic()
    
    print(f"\n===========================")
    print("Diagnostics Complete.")