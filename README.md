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

## Current Status: Phase 1 (Completed)

### Phase 1: Video Pipeline (Completed)
- Implemented `VideoThread` in `core/video.py` for asynchronous 4K capture.
- Implemented `MainWindow` in `gui/window.py` for dynamic video rendering.
- Established signal/slot communication to prevent GUI freezing.

### Phase 0: Planning (Completed)
- Project structure established.
- Core modules defined.

