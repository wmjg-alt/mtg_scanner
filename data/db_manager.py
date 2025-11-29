import sqlite3
import json
import os
import logging
from datetime import datetime
import config

class DBManager:
    def __init__(self):
        self.db_path = config.DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Catalog: Global Card Data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS catalog (
                normalized_name TEXT PRIMARY KEY, scryfall_id TEXT, display_name TEXT,
                set_code TEXT, set_name TEXT, collector_number TEXT, rarity TEXT,
                mana_cost TEXT, cmc REAL, type_line TEXT, oracle_text TEXT,
                power TEXT, toughness TEXT, colors TEXT, legalities TEXT, artist TEXT,
                image_url TEXT, price_usd REAL, price_foil REAL, scryfall_uri TEXT,
                last_fetched TIMESTAMP
            )
        ''')
        # Collection: User Inventory
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS collection (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracker_id TEXT, normalized_name TEXT, date_scanned TIMESTAMP,
                local_image_path TEXT,
                FOREIGN KEY(normalized_name) REFERENCES catalog(normalized_name)
            )
        ''')
        # Aliases: OCR Learning
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS aliases (
                input_text TEXT PRIMARY KEY, real_name TEXT, last_checked TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    # --- CORE METHODS (Keep previous logic) ---
    def get_catalog_card(self, name):
        normalized = name.lower().strip()
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM catalog WHERE normalized_name = ?", (normalized,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def add_to_catalog(self, data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        prices = data.get('prices', {})
        uris = data.get('image_uris', {})
        cursor.execute('''
            INSERT OR REPLACE INTO catalog (
                normalized_name, scryfall_id, display_name, set_code, set_name, collector_number, rarity,
                mana_cost, cmc, type_line, oracle_text, power, toughness, colors, legalities, artist,
                image_url, price_usd, price_foil, scryfall_uri, last_fetched
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['name'].lower(), data.get('id'), data.get('name'), data.get('set'), data.get('set_name'),
            data.get('collector_number'), data.get('rarity'), data.get('mana_cost'), data.get('cmc'),
            data.get('type_line'), data.get('oracle_text'), data.get('power'), data.get('toughness'),
            json.dumps(data.get('colors', [])), json.dumps(data.get('legalities', {})), data.get('artist'),
            uris.get('normal'), prices.get('usd'), prices.get('usd_foil'), data.get('scryfall_uri'),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()

    def get_alias(self, ocr_text):
        normalized = ocr_text.lower().strip()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT real_name FROM aliases WHERE input_text = ?", (normalized,))
        row = cursor.fetchone()
        conn.close()
        if row: return row[0] if row[0] is not None else False
        return None

    def add_alias(self, ocr_text, real_name):
        normalized_in = ocr_text.lower().strip()
        normalized_real = real_name.lower().strip() if real_name else None
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO aliases (input_text, real_name, last_checked) VALUES (?, ?, ?)', 
                       (normalized_in, normalized_real, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def update_scan(self, tracker_id, name, local_path):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, local_image_path FROM collection WHERE tracker_id = ?", (tracker_id,))
        row = cursor.fetchone()
        if row:
            old_path = row[1]
            if old_path and os.path.exists(old_path) and old_path != local_path:
                try: os.remove(old_path)
                except: pass
            cursor.execute('''UPDATE collection SET normalized_name=?, local_image_path=?, date_scanned=? WHERE tracker_id=?''',
                           (name.lower(), local_path, datetime.now().isoformat(), tracker_id))
        else:
            cursor.execute('''INSERT INTO collection (tracker_id, normalized_name, date_scanned, local_image_path) VALUES (?, ?, ?, ?)''',
                           (tracker_id, name.lower(), datetime.now().isoformat(), local_path))
        conn.commit()
        conn.close()

    def delete_scan(self, tracker_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT local_image_path FROM collection WHERE tracker_id = ?", (tracker_id,))
        row = cursor.fetchone()
        if row and row[0] and os.path.exists(row[0]):
            try: os.remove(row[0])
            except: pass
        cursor.execute("DELETE FROM collection WHERE tracker_id = ?", (tracker_id,))
        conn.commit()
        conn.close()

    # --- DASHBOARD & ANALYTICS QUERIES ---

    def get_collection_summary(self):
        """Returns (count, total_value) for the live scanner status bar"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*), SUM(c.price_usd)
            FROM collection col
            JOIN catalog c ON col.normalized_name = c.normalized_name
        """)
        row = cursor.fetchone()
        conn.close()
        count = row[0] if row[0] else 0
        val = row[1] if row[1] else 0.0
        return count, val

    def get_dashboard_stats(self):
        """Aggregate stats for dashboard"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        stats = {}
        
        # Totals
        cursor.execute("SELECT COUNT(*), SUM(c.price_usd) FROM collection col JOIN catalog c ON col.normalized_name = c.normalized_name")
        row = cursor.fetchone()
        stats['total_count'] = row[0] if row[0] else 0
        stats['total_value'] = round(row[1], 2) if row[1] else 0.00
        
        # Top Card
        cursor.execute("""
            SELECT c.display_name, c.price_usd, col.local_image_path, col.tracker_id
            FROM collection col
            JOIN catalog c ON col.normalized_name = c.normalized_name
            ORDER BY c.price_usd DESC LIMIT 1
        """)
        top = cursor.fetchone()
        stats['top_card'] = dict(top) if top else None
        
        # Colors
        cursor.execute("SELECT c.colors FROM collection col JOIN catalog c ON col.normalized_name = c.normalized_name")
        rows = cursor.fetchall()
        color_counts = {"W": 0, "U": 0, "B": 0, "R": 0, "G": 0, "Multi": 0, "Colorless": 0}
        for r in rows:
            try:
                colors = json.loads(r['colors'])
                if not colors: color_counts["Colorless"] += 1
                elif len(colors) > 1: color_counts["Multi"] += 1
                else: color_counts[colors[0]] += 1
            except: pass
        stats['colors'] = color_counts
        
        conn.close()
        return stats

    def get_cards_by_filter(self, color=None, limit=50):
        """Get list of cards, optionally filtered by color"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT col.tracker_id, c.display_name, c.price_usd, col.local_image_path, c.colors
            FROM collection col
            JOIN catalog c ON col.normalized_name = c.normalized_name
        """
        params = []
        
        if color:
            # Simple JSON string matching for single colors. 
            # Multi/Colorless requires logic handled in Python or complex SQL.
            # For simplicity:
            if color in ["W", "U", "B", "R", "G"]:
                query += f" WHERE c.colors LIKE ?"
                params.append(f'%"{color}"%') # Look for "B" in ["U", "B"]
            elif color == "Colorless":
                query += " WHERE c.colors = '[]'"
            # 'Multi' is harder with simple LIKE, we'll skip complex filter for now
            
        query += " ORDER BY col.date_scanned DESC"
        if limit:
            query += f" LIMIT {limit}"
            
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_card_details(self, tracker_id):
        """Get full details for detail view"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT col.*, c.*
            FROM collection col
            JOIN catalog c ON col.normalized_name = c.normalized_name
            WHERE col.tracker_id = ?
        """, (tracker_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_recent_scans(self, limit=10):
        """Returns the last N scanned cards for the gallery (as Dicts)"""
        conn = sqlite3.connect(self.db_path)
        
        # CRITICAL FIX: Enable dictionary-like access
        conn.row_factory = sqlite3.Row 
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT col.tracker_id, c.display_name, c.price_usd, col.local_image_path
            FROM collection col
            JOIN catalog c ON col.normalized_name = c.normalized_name
            ORDER BY col.date_scanned DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        # Convert Rows to standard Dicts to prevent future issues
        return [dict(row) for row in rows]