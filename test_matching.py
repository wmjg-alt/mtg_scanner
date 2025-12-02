import cv2
import time
import os
import glob
import logging
from random import choice
import numpy as np
import config
from services.mtg_service import MTGService
from core.printing_matcher import PrintingMatcher

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

api = MTGService()
matcher = PrintingMatcher()

def get_simulated_scan(url, blur=5, bright=10):
    """Downloads a card image and degrades it to look like a webcam scan"""
    import requests
    resp = requests.get(url, headers={"User-Agent": config.API_USER_AGENT})
    arr = np.frombuffer(resp.content, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    # Degrade
    img = cv2.GaussianBlur(img, (blur, blur), 0)
    img = cv2.convertScaleAbs(img, alpha=1.1, beta=bright)
    return img

def run_the_test(card, candidates):
    print("Running Matcher...") 
    start = time.time()
    winner = matcher.find_best_match(card, candidates)
    elapsed = time.time() - start
    
    print(f"Winner: {winner['set_name']} ({winner['set']})")
    print(f"Processed {len(candidates)} comparisons in {elapsed:.2f}s ({elapsed/len(candidates):.3f}s per card)")

    return winner

def check_success(winner, expected_set):
    if winner['set'] == expected_set:
        print(f"✅ SUCCESS: Correct match on {expected_set}.")
    else:
        print(f"❌ FAIL: Matched {winner['set']} instead of {expected_set}.")

def test_difficult_match(card_name="Iron Myr"):
    print(f"\n--- TEST 1: The {card_name} Dilemma ---")

    candidates = api.search_all_printings(card_name)
    
    card = choice(candidates)
    
    user_scan = get_simulated_scan(card['image_uris']['normal'], blur=7, bright=15)
    
    winner = run_the_test(user_scan, candidates)
    
    check_success(winner, card['set'])

def real_scan_test(card_name, file_name, expected_set):
    print(f"\n--- TEST: Real Scan of {card_name} ---")
    
    scan_path = os.path.join(config.SCANS_DIR, file_name)
    print(f"Loading local scan: {file_name}")
    user_scan = cv2.imread(scan_path)
    
    candidates = api.search_all_printings(card_name)
    
    winner = run_the_test(user_scan, candidates)

    check_success(winner, expected_set)
    

def test_stress_performance():
    print("\n--- TEST 3: Performance Stress (Giant Growth - ~40 Prints) ---")
    from random import choice

    card_name = "Giant Growth"
    candidates = api.search_all_printings(card_name)
    
    # Pick a random one to simulate
    target = choice(candidates)
    print(f"Simulating scan for: {target['set_name']} ({target['set']})")
    user_scan = get_simulated_scan(target['image_uris']['normal'])
    
    winner = run_the_test(user_scan, candidates)
    
    check_success(winner, target['set'])

if __name__ == "__main__":
    test_difficult_match()

    # homelands #47b print of feast of the unicorn
    feast_local = os.path.join(config.SCANS_DIR, "FeastoftheUnicorn_1764551318_C6M36.jpg")
    real_scan_test("Feast of the Unicorn", feast_local, "hml")

    # som scan of leaden myr data\scans\LeadenMyr_1764537501_E9RXA.jpg
    leaden_local = os.path.join(config.SCANS_DIR, "LeadenMyr_1764537501_E9RXA.jpg")
    real_scan_test("Leaden Myr", leaden_local, "som")

    # theros version ofdata\scans\NyleasPresence_1764543583_ZQM6L.jpg
    nylp_local = os.path.join(config.SCANS_DIR, "NyleasPresence_1764543583_ZQM6L.jpg")
    real_scan_test("Nylea's Presence", nylp_local, "ths")

    # mdr scan of iron myr 
    iron_local = os.path.join(config.SCANS_DIR, "IronMyr_1764464396_NDJ9B.jpg")
    real_scan_test("Iron Myr", iron_local, "mrd")

    test_stress_performance()