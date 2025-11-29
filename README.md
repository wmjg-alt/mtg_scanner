# MTG Live Scanner

A sophisticated computer vision pipeline for cataloging Magic: The Gathering cards. This application uses live video to detect cards, tracks them in real-time, reads their titles using enhanced OCR, identifies them via the Scryfall API, and builds a local visual database of your collection.

## Features

### 1. Live Detection & Tracking
- **YOLOv8 Custom Model:** Specifically trained to detect MTG cards on a desk, ignoring background noise.
- **Centroid Tracking:** Assigns a persistent ID to every card. Tracks cards as they slide across the table.
- **Stability Logic:** Only triggers scanning when a card is stationary, ensuring crisp images.

### 2. Intelligent Scanning
- **Smart Warping:** Automatically detects card corners and aspect ratio (Portrait vs Landscape) to flatten skewed cards into perfect rectangles.
- **Enhanced OCR:** Uses EasyOCR with a custom preprocessing pipeline (CLAHE + Upscaling) to read difficult text (e.g., white text on blue backgrounds).
- **Orientation Consensus:** Automatically determines if a card is upside-down or sideways by scoring text legibility across 4 rotations.

### 3. The "Librarian" (Integration)
- **Fluid Database:** The system updates card entries in real-time. A "Scanning..." placeholder evolves into a confirmed card as confidence improves.
- **Scryfall Integration:** Fetches prices, full text, and official artwork.
- **Smart Caching:** 
    - **Resolution Cache:** Remembers corrections (e.g., "Nyxbora" -> "Nyxborn Wolf").
    - **Negative Cache:** Remembers invalid text to prevent repeated API failures.
    - **Image Cache:** Downloads official art once to save bandwidth.

### 4. Collection Dashboard
- **Interactive Analytics:** Pie charts for Color distribution, Total Value tracking, and "Top Card" highlighting.
- **Visual Gallery:** View your scans side-by-side with official high-res art.
- **Management:** Click any card to view deep details or delete errors from the collection.

---

## Setup & Usage

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Requires CUDA-enabled PyTorch for optimal performance.*

2. **Run the Application:**
   ```bash
   python main.py
   ```
   *   **Scanner Mode:** Opens first. Place cards under the camera.
   *   **Dashboard Mode:** Opens automatically when you close the scanner.

3. **Command Line Flags:**
   - `python main.py --scanner-only`: Run only the capture loop.
   - `python main.py --report`: Skip capture, open the Dashboard immediately.

----

## Changelog and Status: Phase 8

#### Phase 8: Dashboard & Polish (Current)
- **Interactive Dashboard**: Added a PySide6 visual interface for browsing the collection.
- **Image Caching**: Implemented local caching for web images to improve performance.
- **Detail View**: Added side-by-side comparison (Local Scan vs Official Art) and deletion capabilities.
- **CLI Flags**: Added support for --report and --scanner-only modes.

#### Phase 7: Grand Unification (COMPLETE)
- **Pipeline Integration**: Connected Video Thread, Tracker, Librarian, and GUI into a single reactive loop.
- **Fluid Updates**: Database now supports UPSERT logic, allowing a card's identity to refine over time without creating duplicate entries.
- **Visual Widgets**: Added ActiveCardWidget to the live feed, displaying real-time OCR confidence and pricing 
- **Quality Gates**: Implemented logic to only save a new scan if it has a higher confidence score than the previous best for that object ID.


#### Phase 7: The Grand Unification (COMPLETE)
- **Fluid Database:** Implemented `UPSERT` logic in `db_manager.py` allowing card identity to evolve as OCR improves (e.g., "Scanning..." "OCR: Woll"-> "Wool Demon" -> "Nyxborn Wolf").
- **Reactive GUI:** Built `ActiveCardWidget` to display live cards with dynamic status updates.
- **Pipeline Integration:**
    - `VideoThread` tracks objects (Red IDs) and triggers scans every 1s.
    - `Librarian` processes scans in background: OCR -> Cache -> API -> DB.
    - `StatsManager` persists "Total Objects Seen" and generates alphanumeric IDs.

#### Phase 6: Librarian & API (COMPLETE)
- **Database (`data/db_manager.py`):** 
    - Implemented SQLite schema separating `catalog` (Scryfall cache) from `collection` (User scans).
- **API (`services/scryfall_service.py`):**
    - Strict 1.0s rate limiting.
    - Uses Scryfall Fuzzy Matching to handle OCR typos.
- **Controller (`core/librarian.py`):**
    - Background thread processing the identification queue.
    - Logic: Check DB -> If Missing, Check API -> Save Scan -> Log to Collection.

#### Phase 5: Image Processing & OCR (COMPLETE)
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

#### Phase 4: Custom Model Training (COMPLETE)
- Created `tools/capture_data.py` to harvest training images.
- **Goal:** Train a custom YOLOv8 model on specific MTG card data.
- **Why:** Generic model required 3% confidence and NMS hacks. Custom model should allow greater confidence.
    - data/models/best.pt
- **Method:** command:

    ```yolo task=detect mode=train model=yolov8n.pt data=dataset/formatted/data.yaml epochs=50 imgsz=640 plots=True```

#### Phase 3: Object Tracking (COMPLETE)
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

#### Phase 2: Detection w/ some Tuning (COMPLETE)
- Refactored file structure: Moved ML models to `data/models/`.
- Updated `config.py` to use relative paths.
- **Tuning:** Lowered YOLO confidence threshold to 0.25 to detect stationary cards.
- **Filtering:** Restricted YOLO detection to 'book' and 'cell phone' classes to ignore background noise (mice, keyboards, card art).
- Added debug visualization overlay.

#### Phase 1: Video Pipeline (COMPLETE)
- Implemented `VideoThread` in `core/video.py` for asynchronous 4K capture.
- Implemented `MainWindow` in `gui/window.py` for dynamic video rendering.
- Established signal/slot communication to prevent GUI freezing.

#### Phase 0: Planning (COMPLETE)
- Project structure established.
- Core modules defined.

### GPU Setup Potential Issue (Error Encountered)
If you see `NotImplementedError: torchvision::nms`, it means your PyTorch and Torchvision versions are mismatched (one is CPU, one is GPU).

To fix this, force a reinstall of the CUDA-enabled versions:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130 --force-reinstall
