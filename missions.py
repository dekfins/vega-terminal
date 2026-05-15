# missions.py
import random
from database import get_random_component, get_location, get_random_loot

def calculate_payout(difficulty, distance_au):
    """Calculates flat credits and applies ANSI-colored loot drops."""
    # 1. Base Credit Math
    base_fee = 2000
    au_rate = 1500
    hazard_mult = 1.0 + (difficulty * 0.2)
    
    raw_credits = (base_fee + (distance_au * au_rate)) * hazard_mult
    variance = random.uniform(0.95, 1.05)
    final_payout = raw_credits * variance
    
    payout_string = f"{final_payout:,.0f} CR"
    
    # 2. The Loot Drop (50% chance the client offers a gear bonus)
    if random.random() > 0.50:
        rarity, item = get_random_loot(difficulty)
        
        # ANSI Color Mapping
        colors = {
            "common": "\u001b[0;37m",    # White
            "uncommon": "\u001b[0;32m",  # Green
            "rare": "\u001b[0;34m",      # Blue
            "epic": "\u001b[0;35m",      # Purple
            "legendary": "\u001b[0;33m"  # Yellow
        }
        color_code = colors.get(rarity, "\u001b[0;37m")
        payout_string += f" + {color_code}{item}\u001b[0m"
        
    return payout_string

# Update the parameters to require distance_au instead of transit_days
def roll_single_seed(origin, target, transit_days, food_days, dv_req, dv_avail, heat_state, distance_au, diff_range=(1, 10)):
    target_diff = random.randint(diff_range[0], diff_range[1])
    
    client = get_random_component("clients")
    objective = get_random_component("objectives")
    adversary = get_random_component("adversaries")
    twist = get_random_component("complications")
    loc = get_location(target)
    
    # Pass distance_au into the new calculation
    payout = calculate_payout(target_diff, distance_au)
    
    hook_text = (
        f"\u001b[0;32mROUTE:\u001b[0m {origin} ➔ {target} ({transit_days:.1f}d)\n"
        f"\u001b[0;32mLOGISTICS:\u001b[0m {dv_avail:.0f}/{dv_req:.2f} km/s dV\n"
        f"\u001b[0;32mPAYOUT:\u001b[0m {payout}\n\n"
        f"\u001b[0;34m[CLIENT]\u001b[0m {client}\n"
        f"\u001b[0;34m[OBJECTIVE]\u001b[0m {objective}\n"
        f"\u001b[0;34m[LOCATION]\u001b[0m {loc}\n"
        f"\u001b[0;34m[ADVERSARY]\u001b[0m {adversary}\n"
        f"\u001b[0;31m[TWIST]\u001b[0m {twist}"
    )

    return {
        "origin": origin, "target": target, "difficulty": target_diff,
        "transit_days": transit_days, "dv_req": dv_req, "dv_avail": dv_avail,
        "client": client, "objective": objective, "location": loc,
        "adversary": adversary, "twist": twist, "payout": payout,
        "text": hook_text
    }

