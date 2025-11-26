import os

# --- PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "data", "models", "best.pt")

# --- CAMERA SETTINGS ---
CAMERA_INDEX = 0
REQUEST_WIDTH = 3840          
REQUEST_HEIGHT = 2160         

# --- DETECTION SETTINGS ---
YOLO_MODEL = MODEL_PATH       
YOLO_INPUT_SIZE = 640       
CONFIDENCE_THRESHOLD = 0.7  
DETECT_EVERY_N_FRAMES = 1  #  5 better for performance, 1 for rapid movements

# --- FILTERING RULES ---
NMS_THRESHOLD = 0.3          
CONTAINMENT_THRESHOLD = 0.85 

# --- LOGIC RULES ---
EDGE_MARGIN = 50            
MIN_BOX_WIDTH = 50           
MIN_BOX_HEIGHT = 70          

# --- DEBUG / VISUALIZATION ---
SHOW_DEBUG_BOXES = True     
SHOW_EDGE_BORDER = True     
DEBUG_COLOR_BOX = (0, 255, 0)       
DEBUG_COLOR_BORDER = (0, 0, 255)

# --- TRACKING SETTINGS ---
MAX_TRACKING_DISTANCE = 1000  
MAX_DISAPPEARED_FRAMES = 15   
MIN_FRAMES_TO_CONFIRM = 15    

# --- STABILITY SETTINGS ---
STABILITY_DISTANCE = 15      
STABILITY_HISTORY_LEN = 10