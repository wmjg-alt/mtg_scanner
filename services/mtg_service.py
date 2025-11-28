import requests
import time
import urllib.parse
import config

class MTGService:
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