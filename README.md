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

## Current Status: Phase 3

### Phase 3: Object Tracking (...)
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

