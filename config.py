import os

# --- PATHS ---
# Robust way to find the model relative to this config file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "data", "models", "yolov8n.pt")

# --- CAMERA SETTINGS ---
CAMERA_INDEX = 0
REQUEST_WIDTH = 3840          
REQUEST_HEIGHT = 2160         

# --- DETECTION SETTINGS ---
YOLO_MODEL = MODEL_PATH       # Updated to use the variable above
YOLO_INPUT_SIZE = 640       
CONFIDENCE_THRESHOLD = 0.25   # Kept low based on testing
DETECT_EVERY_N_FRAMES = 5   

# --- LOGIC RULES ---
EDGE_MARGIN = 50            
MIN_BOX_WIDTH = 50           
MIN_BOX_HEIGHT = 70          

# --- DEBUG / VISUALIZATION ---
SHOW_DEBUG_BOXES = True     
SHOW_EDGE_BORDER = True     
DEBUG_COLOR_BOX = (0, 255, 0)       
DEBUG_COLOR_BORDER = (0, 0, 255)