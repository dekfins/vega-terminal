# database.py
import json
import random
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "database.json")

# 1. Boot Sequence: Load Data
try:
    with open(JSON_PATH, "r", encoding="utf-8") as file:
        DB = json.load(file)
except FileNotFoundError:
    print(f"CRITICAL ERROR: {JSON_PATH} not found.")
    DB = {}
except Exception as e:
    print(f"DATABASE BOOT ERROR: {e}")
    DB = {}

def load_db():
    global DB
    with open(JSON_PATH, "r", encoding="utf-8") as file:
        DB = json.load(file)
    return DB

# 2. Component Retrieval
def get_random_component(category):
    """Pulls a random string from a standard category array."""
    try:
        return random.choice(DB[category])
    except (KeyError, IndexError):
        return "[MISSING DATA]"

def get_location(planet):
    """Pulls a random specific location for a given planet."""
    try:
        return random.choice(DB["locations"][planet])
    except (KeyError, IndexError):
        return "Generic Orbital Vector"
    
def get_random_loot(difficulty):
    """Rolls for loot, with higher difficulties pushing the rarity up."""
    try:
        # Base roll 1-100, plus a bonus based on difficulty (max +20)
        roll = random.randint(1, 100) + (difficulty * 2)
        
        if roll >= 95: rarity = "legendary"
        elif roll >= 80: rarity = "epic"
        elif roll >= 60: rarity = "rare"
        elif roll >= 30: rarity = "uncommon"
        else: rarity = "common"
        
        item = random.choice(DB["loot"][rarity])
        return rarity, item
    except KeyError:
        return "common", "a handful of loose credits"
    
def get_random_loot(difficulty):
    # Use difficulty as a stricter gate, not just a small bonus
    roll = random.randint(1, 100)
    
    # Legendary: Only possible at Diff 8+ and a high roll
    if roll + difficulty >= 105: rarity = "legendary"
    # Epic: Only possible at Diff 5+ and a high roll
    elif roll + difficulty >= 95: rarity = "epic"
    elif roll + (difficulty * 2) >= 75: rarity = "rare"
    elif roll + (difficulty * 3) >= 50: rarity = "uncommon"
    else: rarity = "common"
    
    item = random.choice(DB["loot"][rarity])
    return rarity, item

DB = load_db()