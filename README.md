# MTG Live Scanner

A modular Python application to scan Magic the Gathering cards via live webcam, extract their text, look up real-time pricing, and catalog them in a local database.

## Architecture
- **GUI:** PySide6 (Qt)
- **Vision:** OpenCV & YOLOv8
- **OCR:** EasyOCR / Tesseract
- **Data:** SQLite & API Calls

## Setup
1. Create a virtual environment: `python -m venv venv`
2. Activate it.
3. Install requirements: `pip install -r requirements.txt`

## Current Status: Phase 6

### Phase 6: Librarian & API (...)
- **Database (`data/db_manager.py`):** 
    - Implemented SQLite schema separating `catalog` (Scryfall cache) from `collection` (User scans).
- **API (`services/scryfall_service.py`):**
    - Strict 1.0s rate limiting.
    - Uses Scryfall Fuzzy Matching to handle OCR typos.
- **Controller (`core/librarian.py`):**
    - Background thread processing the identification queue.
    - Logic: Check DB -> If Missing, Check API -> Save Scan -> Log to Collection.

### Phase 5: Image Processing & OCR (Completed)
- **Smart Tranform (`core/image_processor.py`):** 
    - Extracts card from YOLO box.
    - Uses contour detection to find card corners.
    - Automatically detects Aspect Ratio (Portrait vs Landscape) to prevent smearing.
    - Performs perspective transform to flatten the image.
- **Smart OCR (`services/ocr_service.py`):**
    - Uses EasyOCR (GPU-accelerated) to read card titles.
    - **Orientation Logic:** Automatically checks 4 orientations (Upright, Inverted, 90° CW, 90° CCW).
    - **Scoring System:** Selects the best text based on Letter Density (Letters * Confidence) to distinguish Titles from Stats.
    - Returns the corrected, upright image for archival.
- **Testing:**
    - `test_phase5.py`: Maps YOLO labels to original 4K images to verify pipeline without "Thumbnail Blur".

### Phase 4: Custom Model Training (COMPLETE)
- Created `tools/capture_data.py` to harvest training images.
- **Goal:** Train a custom YOLOv8 model on specific MTG card data.
- **Why:** Generic model required 3% confidence and NMS hacks. Custom model should allow greater confidence.
    - data/models/best.pt
- **Method:** command:

    ```yolo task=detect mode=train model=yolov8n.pt data=dataset/formatted/data.yaml epochs=50 imgsz=640 plots=True```

### Phase 3: Object Tracking (COMPLETE)
- Implemented `CentroidTracker` in `core/tracker.py`.
- Assigns unique IDs to cards.
- **Features:** 
    - Persistence: Remembers cards even if YOLO misses a frame.
    - History Trails: Visualizes detection stability.
    - Tunable parameters in `config.py` for tracking sensitivity.
    - Added visual "Search Radius" (Yellow Circle) to debug tracking limits.
    - Implemented **NMS (Non-Maximum Suppression)** to merge overlapping boxes.
    - Implemented **Containment Filtering** to remove small false positives inside larger cards.
- **Config:** Added `NMS_THRESHOLD` and `CONTAINMENT_THRESHOLD` to `config.py`.

### Phase 2: Detection w/ some Tuning (COMPLETE)
- Refactored file structure: Moved ML models to `data/models/`.
- Updated `config.py` to use relative paths.
- **Tuning:** Lowered YOLO confidence threshold to 0.25 to detect stationary cards.
- **Filtering:** Restricted YOLO detection to 'book' and 'cell phone' classes to ignore background noise (mice, keyboards, card art).
- Added debug visualization overlay.

### Phase 1: Video Pipeline (COMPLETE)
- Implemented `VideoThread` in `core/video.py` for asynchronous 4K capture.
- Implemented `MainWindow` in `gui/window.py` for dynamic video rendering.
- Established signal/slot communication to prevent GUI freezing.

### Phase 0: Planning (COMPLETE)
- Project structure established.
- Core modules defined.

### GPU Setup Potential Issue (Error Encountered)
If you see `NotImplementedError: torchvision::nms`, it means your PyTorch and Torchvision versions are mismatched (one is CPU, one is GPU).

To fix this, force a reinstall of the CUDA-enabled versions:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130 --force-reinstall
