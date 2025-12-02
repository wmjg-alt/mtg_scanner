import requests
import time
import urllib.parse
import logging
import config

class MTGService:
    """
    Handles communication with Scryfall API.
    Enforces rate limits and user-agent requirements.
    """
    def __init__(self):
        self.base_url = config.API_BASE_URL
        self.last_request_time = 0
        self.min_delay = config.API_RATE_LIMIT
        
        self.headers = {
            "User-Agent": config.API_USER_AGENT,
            "Accept": "*/*"
        }

    def _wait_for_rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_request_time = time.time()

    def get_card_by_name(self, query_text):
        """
        Fuzzy lookup for a single card (Fast Path).
        Returns the default/most recent printing.
        """
        self._wait_for_rate_limit()
        
        safe_query = urllib.parse.quote(query_text)
        url = f"{self.base_url}/cards/named?fuzzy={safe_query}"
        
        print(f"[API] Requesting: {query_text}...")
        try:
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                print("[API] Success.")
                return response.json()
            elif response.status_code == 404:
                print(f"[API] Card not found: {query_text}")
                return None
            else:
                print(f"[API] Error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"[API] Connection Failure: {e}")
            return None

    def search_all_printings(self, card_name):
        """
        Fetches ALL unique paper printings of a card name.
        Used for Visual Fingerprinting/Matching.
        """
        self._wait_for_rate_limit()
        
        # Syntax: !"Card Name" (Exact) + unique:prints + game:paper
        query = f'!"{card_name}" unique:prints game:paper'
        safe_query = urllib.parse.quote(query)
        
        url = f"{self.base_url}/cards/search?q={safe_query}"
        
        try:
            logging.info(f"[API] Searching printings for: {card_name}")
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                # If there are pages (unlikely for most cards except basics), 
                # we only take the first page (175 cards) for performance.
                return data.get('data', [])
            else:
                logging.error(f"[API] Search Error {response.status_code}: {response.text}")
                return []
        except Exception as e:
            logging.error(f"[API] Connection Failure: {e}")
            return []