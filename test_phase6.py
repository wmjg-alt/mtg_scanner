import time
import sqlite3
import os
import numpy as np
import config
from core.librarian import Librarian

def print_db_stats():
    """Reads the SQLite DB and prints a detailed summary"""
    if not os.path.exists(config.DB_PATH):
        print(f"❌ Database not found at {config.DB_PATH}")
        return

    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row # Access by name
    cursor = conn.cursor()

    print("\n" + "="*80)
    print(f"📊 DATABASE DEEP INSPECTION")
    print("="*80)

    # --- 1. CATALOG ---
    cursor.execute("SELECT * FROM catalog")
    rows = cursor.fetchall()
    print(f"\n[CATALOG] - {len(rows)} Unique Cards")
    
    for row in rows:
        print(f"\n  🃏 {row['display_name']} ({row['set_code'].upper()})")
        print(f"     Type:   {row['type_line']}")
        print(f"     Mana:   {row['mana_cost']} (CMC {row['cmc']})")
        print(f"     Stats:  {row['power']}/{row['toughness']}")
        print(f"     Oracle: {row['oracle_text'][:60]}..." if row['oracle_text'] else "     Oracle: None")
        print(f"     Artist: {row['artist']}")
        print(f"     Price:  ${row['price_usd']} (Foil: ${row['price_foil']})")
        print(f"     ImgURL: {row['image_url']}")

    # --- 2. ALIASES ---
    cursor.execute("SELECT input_text, real_name FROM aliases")
    rows = cursor.fetchall()
    print(f"\n[ALIASES] - {len(rows)} Learned Corrections")
    for row in rows:
        arrow = f"-> {row['real_name']}" if row['real_name'] else "-> ❌ INVALID"
        print(f"  '{row['input_text']}' {arrow}")

    print("\n" + "="*80 + "\n")
    conn.close()

def test_librarian():
    # Optional: Start fresh
    if os.path.exists(config.DB_PATH):
        os.remove(config.DB_PATH)
        print("🗑️  Fresh DB for testing.")

    librarian = Librarian()
    librarian.start()
    
    # Mock Image
    dummy_img = np.zeros((630, 880, 3), dtype=np.uint8)
    
    def on_found(name, price, path):
        print(f"✅ GUI SIGNAL: {name} ({price})")

    librarian.card_found_signal.connect(on_found)

    print("\n--- Test 1: Full Ingestion ---")
    print("Asking API for 'Nyxborn Wolf'...")
    librarian.add_task("Nyxborn Wolf", dummy_img)
    time.sleep(3) # Wait for API

    print("\n--- Test 2: Typo Handling ---")
    print("Asking for 'Nyxbora Wolf'...")
    librarian.add_task("Nyxbora Wolf", dummy_img)
    time.sleep(1)

    print("\n--- Test 3: Negative Cache ---")
    librarian.add_task("FakeCardName123", dummy_img)
    time.sleep(2)
    librarian.add_task("FakeCardName123", dummy_img)
    time.sleep(0.5)

    librarian.stop()
    print_db_stats()

if __name__ == "__main__":
    test_librarian()