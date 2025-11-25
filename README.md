# MTG Live Scanner

A modular Python application to scan Magic the Gathering cards via live webcam, extract their text, look up real-time pricing via Scryfall, and catalog them in a local database.

## Architecture
- **GUI:** PySide6 (Qt)
- **Vision:** OpenCV & YOLOv8
- **OCR:** EasyOCR / Tesseract
- **Data:** SQLite & Scryfall API

## Setup
1. Create a virtual environment: `python -m venv venv`
2. Activate it.
3. Install requirements: `pip install -r requirements.txt`

## Current Status: Phase 0 (Planning)
- Project structure established.
- Core modules defined.