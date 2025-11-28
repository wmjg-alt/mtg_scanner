import sqlite3
import json
import os
from datetime import datetime
import config

class DBManager:
    def __init__(self):
        self.db_path = config.DB_PATH
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 1. CATALOG (Global Knowledge)
        # Expanded to hold deep data: Mana, Oracle Text, Set info, etc.
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS catalog (
                normalized_name TEXT PRIMARY KEY,
                scryfall_id TEXT,
                display_name TEXT,
                set_code TEXT,
                set_name TEXT,
                collector_number TEXT,
                rarity TEXT,
                mana_cost TEXT,
                cmc REAL,
                type_line TEXT,
                oracle_text TEXT,
                power TEXT,
                toughness TEXT,
                colors TEXT,       -- Stored as JSON ["G", "U"]
                legalities TEXT,   -- Stored as JSON
                artist TEXT,
                image_url TEXT,    -- The high-res Scryfall image
                price_usd REAL,
                price_foil REAL,
                scryfall_uri TEXT,
                last_fetched TIMESTAMP
            )
        ''')

        # 2. COLLECTION (Your Inventory)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collection (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                normalized_name TEXT,
                date_scanned TIMESTAMP,
                local_image_path TEXT,
                FOREIGN KEY(normalized_name) REFERENCES catalog(normalized_name)
            )
        ''')

        # 3. ALIASES (The Brain)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS aliases (
                input_text TEXT PRIMARY KEY,
                real_name TEXT,
                last_checked TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_catalog_card(self, name):
        """Get full card details if available."""
        normalized = name.lower().strip()
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row # Allows accessing columns by name
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM catalog WHERE normalized_name = ?", (normalized,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row) # Convert Row object to standard dict
        return None

    def add_to_catalog(self, data):
        """
        Parses the raw Scryfall JSON and inserts into the catalog.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Helper to extract deep nested keys safely
        prices = data.get('prices', {})
        uris = data.get('image_uris', {})
        
        # Prepare complex fields as JSON strings
        colors_json = json.dumps(data.get('colors', []))
        legalities_json = json.dumps(data.get('legalities', {}))

        cursor.execute('''
            INSERT OR REPLACE INTO catalog (
                normalized_name, scryfall_id, display_name, 
                set_code, set_name, collector_number, rarity,
                mana_cost, cmc, type_line, oracle_text,
                power, toughness, colors, legalities, artist,
                image_url, price_usd, price_foil, scryfall_uri,
                last_fetched
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['name'].lower(),
            data.get('id'),
            data.get('name'),
            data.get('set'),
            data.get('set_name'),
            data.get('collector_number'),
            data.get('rarity'),
            data.get('mana_cost'),
            data.get('cmc'),
            data.get('type_line'),
            data.get('oracle_text'),
            data.get('power'),
            data.get('toughness'),
            colors_json,
            legalities_json,
            data.get('artist'),
            uris.get('normal'), # Use 'normal' size for general display
            prices.get('usd'),
            prices.get('usd_foil'),
            data.get('scryfall_uri'),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()

    def log_scan(self, name, local_path):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO collection (normalized_name, date_scanned, local_image_path)
            VALUES (?, ?, ?)
        ''', (name.lower(), datetime.now().isoformat(), local_path))
        conn.commit()
        conn.close()
        print(f"[DB] Logged scan to collection: {name}")

    # --- ALIAS METHODS ---
    def get_alias(self, ocr_text):
        normalized_input = ocr_text.lower().strip()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT real_name FROM aliases WHERE input_text = ?", (normalized_input,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0] if row[0] is not None else False
        return None

    def add_alias(self, ocr_text, real_name):
        normalized_input = ocr_text.lower().strip()
        normalized_real = real_name.lower().strip() if real_name else None
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO aliases (input_text, real_name, last_checked)
            VALUES (?, ?, ?)
        ''', (normalized_input, normalized_real, datetime.now().isoformat()))
        conn.commit()
        conn.close()