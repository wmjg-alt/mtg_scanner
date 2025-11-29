import json
import os
import logging
import random
import string
import config

# Setup Logging
logging.basicConfig(
    filename=config.LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class StatsManager:
    def __init__(self):
        self.stats = {
            "total_objects_seen": 0,
            "session_start_ts": 0
        }
        self.load_stats()

    def load_stats(self):
        if os.path.exists(config.STATS_FILE):
            try:
                with open(config.STATS_FILE, 'r') as f:
                    self.stats = json.load(f)
            except:
                pass # Corrupt file, start fresh

    def save_stats(self):
        with open(config.STATS_FILE, 'w') as f:
            json.dump(self.stats, f)

    def increment_objects_seen(self):
        self.stats["total_objects_seen"] += 1
        self.save_stats()
        return self.stats["total_objects_seen"]

    def generate_id(self):
        """Generates a unique 5-digit alphanumeric ID"""
        # Uppercase + Digits
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=5))