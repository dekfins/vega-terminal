# app.py
import streamlit as st
import json
import random
import physics as phys
import missions
import database
from discord_webhook import DiscordWebhook, DiscordEmbed
import re

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1501123316801601628/4WanEF8oV9YLT9iH34p0hYDL5oICvUGm5-Gv7rZaWPDo5OxZUe8MjXB_TyRxn7nslL1M"
STATE_FILE = "state.json"
PLANETS_FILE = "planets.json"

def clean_ansi(text):
    """Removes ANSI escape codes for clean web display."""
    return re.sub(r'\u001b\[[0-9;]*m', '', str(text))

def load_json(filepath):
    with open(filepath, "r") as f:
        return json.load(f)

# --- BOOT & STATE MANAGEMENT ---
if 'initialized' not in st.session_state:
    raw_state = load_json(STATE_FILE)
    st.session_state.planets = load_json(PLANETS_FILE)
    st.session_state.current_day = raw_state["campaign"]["current_day"]
    st.session_state.food_days = raw_state["ship"]["food_days"]
    st.session_state.argon_units = raw_state["ship"]["fuel_cells"]["argon_units"]
    st.session_state.xenon_units = raw_state["ship"]["fuel_cells"]["xenon_units"]
    st.session_state.active_fuel_cell = raw_state["ship"]["active_fuel_cell"]
    for k, v in raw_state["heat"].items():
        st.session_state[f"heat_{k}"] = v
    st.session_state.initialized = True

def sync_to_disk():
    updated_state = {
        "campaign": {"current_day": st.session_state.current_day},
        "ship": {
            "name": "The Toe-Tickler",
            "food_days": st.session_state.food_days,
            "active_fuel_cell": st.session_state.active_fuel_cell,
            "base_accel_g": 0.05,
            "fuel_cells": {
                "argon_units": st.session_state.argon_units,
                "xenon_units": st.session_state.xenon_units
            }
        },
        "heat": {k: st.session_state[f"heat_{k}"] for k in ["tac", "dave", "scum", "jerk", "pos"]}
    }
    with open(STATE_FILE, "w") as f:
        json.dump(updated_state, f, indent=4)

def render_discord_preview(text):
    """Converts raw ANSI codes into Discord-accurate HTML for the Streamlit UI."""
    import re
    
    # Map ANSI codes to Discord's specific hex UI colors
    replacements = {
        r'\u001b\[0;32m': "<span style='color: #57F287;'>", # Discord Green
        r'\u001b\[0;34m': "<span style='color: #5865F2;'>", # Discord Blue
        r'\u001b\[0;31m': "<span style='color: #ED4245;'>", # Discord Red
        r'\u001b\[0;37m': "<span style='color: #FFFFFF;'>", # White
        r'\u001b\[0;33m': "<span style='color: #FEE75C;'>", # Yellow
        r'\u001b\[0;35m': "<span style='color: #EB459E;'>", # Purple
        r'\u001b\[0m': "</span>" # Reset tag
    }
    
    # Strip the markdown code fences for the preview
    html_text = text.replace("```ansi\n", "").replace("```", "")
    
    for ansi, html_tag in replacements.items():
        html_text = re.sub(ansi, html_tag, html_text)
        
    html_text = html_text.replace("\n", "<br>")
    
    # Wrap in a Discord-styled dark mode container
    return f"""
    <div style="background-color: #2b2d31; color: #dbdee1; padding: 12px; 
                border-radius: 6px; font-family: 'Courier New', monospace; 
                font-size: 14px; border: 1px solid #1e1f22; line-height: 1.4;">
        {html_text}
    </div>
    """

# brute force the css
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

        /* 1. FONT OVERRIDES */
        html, body, [data-testid="stAppViewContainer"], .stMarkdown, p, label, input, button, .streamlit-expanderHeader, h1, h2, h3 {
            font-family: "OCR A Extended", "Share Tech Mono", monospace !important;
        }
            
        [data-baseweb="popover"], [data-baseweb="popover"] *, ul[role="listbox"] li {
            font-family: "OCR A Extended", "Share Tech Mono", monospace !important;
        }

        /* 2. LAYOUT COMPRESSION */
        .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; max-width: 98% !important; }
        header, footer { visibility: hidden; }
        .stExpander { margin-bottom: 0px !important; }
        [data-testid="stExpander"] .stVerticalBlock { gap: 0.2rem !important; }

        /* 3. INPUT BOX "GHOST" STYLING */
        [data-testid="stTextInput"] {
            margin-top: 0px !important;
            margin-bottom: 2px !important;
        }

        /* Target the actual input container to remove the background box */
        [data-testid="stTextInput"] > div[data-baseweb="base-input"], 
        [data-testid="stTextInput"] > div[data-baseweb="input"] {
            background-color: transparent !important;
            border: none !important;
        }

        [data-testid="stExpander"] input {
            background-color: transparent !important;
            border: none !important;
            border-left: 2px solid #39ff14 !important; /* The 'Prompt' cursor */
            border-radius: 0px !important;
            padding-left: 10px !important;
            color: #39ff14 !important;
            height: 32px !important; /* Fixes text cutoff */
        }

        /* Focus state highlight */
        [data-testid="stExpander"] input:focus {
            background-color: #0c1c0c !important; /* Very subtle green-black glow */
            border-left: 2px solid #ffffff !important;
        }

        /* 4. THE BUTTON */
        div.stButton > button {
            background-color: transparent !important;
            color: #39ff14 !important;
            border: none !important;
            padding: 0 !important;
            text-decoration: none !important;
        }
        div.stButton > button:hover { text-decoration: underline !important; }
    </style>
""", unsafe_allow_html=True)

# --- UI LAYOUT ---
st.set_page_config(layout="wide")

st.title("VERY ENTHUSIASTIC GENERAL ASSISTANT")

col_logistics, col_kinematics, col_uplink = st.columns([1, 1, 2])

with col_logistics:
    st.markdown("### LOGISTICS")
    col_log1, col_log2 = st.columns(2)
    with col_log1:
        st.number_input("DAY", value=34, label_visibility="visible")
    with col_log2:
        st.number_input("KIBBLE", value=30, label_visibility="visible")

    st.markdown("### PROPULSION")
    # 1. Assign the selectbox to a variable
    fuel_type = st.selectbox("ACTIVE CELL", ["Argon", "Xenon"], label_visibility="collapsed")
    
    # 2. Assign the number input to a variable (units)
    if fuel_type == "Argon":
        units = st.number_input("ARGON UNITS", value=5.00, step=0.1)
        isp = 100
    else:
        units = st.number_input("XENON UNITS", value=5.00, step=0.1)
        isp = 250
    
    # 3. Perform math using those variables directly
    max_dv = units * isp
    st.markdown(f"**AVAILABLE DELTA-V:** {max_dv:.1f} km/s")

with col_kinematics:
    st.subheader("ORBITAL KINEMATICS")
    origin_name = st.selectbox("ORIGIN NODE", list(st.session_state.planets.keys()), index=0)
    diff_range = st.slider("JOB BOARD DIFFICULTY RANGE", min_value=1, max_value=10, value=(2, 8))
    accel = 0.05 * 9.81
    
    # --- app.py (Calculation Button) ---
    if st.button("CALCULATE & REQUEST BRIEFINGS", type="primary"):
        st.session_state.db = database.load_db()
        st.session_state.batch_id = random.randint(10000, 99999)
        all_destinations = []
        for planet, data in st.session_state.planets.items():
            if planet != origin_name and planet != "Persephone":
                all_destinations.append(planet)
                if "moons" in data:
                    all_destinations.extend(data["moons"])
        
        random.shuffle(all_destinations)
        
        current_seeds = []
        found_missions = 0
        
        for target in all_destinations:
            if found_missions >= 3: break
                
            physics_target = target
            for p, d in st.session_state.planets.items():
                if "moons" in d and target in d["moons"]:
                    physics_target = p
                    break
                    
            p1 = st.session_state.planets[origin_name]
            p2 = st.session_state.planets[physics_target]
            res = phys.solve_trajectory(p1, p2, st.session_state.current_day, accel, max_dv)
            
            seed = missions.roll_single_seed(
                origin=origin_name, 
                target=target, 
                transit_days=res['days'], 
                food_days=st.session_state.food_days,
                dv_req=res['dv_required'], 
                dv_avail=max_dv,
                heat_state=st.session_state,
                distance_au=res['distance_au'],
                diff_range=diff_range
            )
            
            if diff_range[0] <= seed['difficulty'] <= diff_range[1]:
                current_seeds.append(seed)
                found_missions += 1
               
        if found_missions == 0:
            st.error("NO GIGS FOUND IN THAT RANGE.")
        else:
            st.session_state.current_seeds = current_seeds

with col_uplink:
    st.subheader("EDIT & UPLINK")
    edited_seeds = []
    batch = st.session_state.get("batch_id", 0)
    
    if "current_seeds" in st.session_state:
        for i, seed in enumerate(st.session_state.current_seeds):
            # Clean header: M# | Target | Payout
            header = f"Mission {i+1}: {seed['origin']} > {seed['target']}, D:{seed['difficulty']} T:{seed['transit_days']:.2f}"
            with st.expander(header, expanded=True):
                # 2 columns provide enough width for the strings
                c1, c2 = st.columns(2)
                with c1:
                    new_client = st.text_input("Client", value=seed['client'], key=f"c_{batch}_{i}", label_visibility="visible")
                    new_obj = st.text_input("Objective", value=seed['objective'], key=f"o_{batch}_{i}", label_visibility="visible")
                    new_loc = st.text_input("Location", value=seed['location'], key=f"l_{batch}_{i}", label_visibility="visible")
                with c2:
                    new_adv = st.text_input("Adversaries", value=seed['adversary'], key=f"a_{batch}_{i}", label_visibility="visible")
                    new_twist = st.text_input("Twist", value=seed['twist'], key=f"t_{batch}_{i}", label_visibility="visible")
                    new_pay = st.text_input("Payout", value=seed['payout'], key=f"p_{batch}_{i}", label_visibility="visible")

                edited_seeds.append({**seed, "client": new_client, "objective": new_obj, "location": new_loc, "adversary": new_adv, "twist": new_twist, "payout": new_pay})
                pass

        if st.button("TRANSMIT TO DISCORD", use_container_width=True):
            try:
                webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL)
                webhook.content = "**[VEGA UPLINK INITIATED]**"

                def get_diff_color(diff):
                    if diff <= 3: return 0x00FF00
                    if diff <= 7: return 0xFFA500
                    return 0xFF0000

                # Assemble the ANSI codes at the absolute last second
                for seed in edited_seeds:
                    hook_text = (
                        f"\u001b[0;32mDIFFICULTY:\u001b[0m {seed['difficulty']}\n"
                        f"\u001b[0;32mROUTE:\u001b[0m {seed['origin']} ➔ {seed['target']}\n"
                        f"\u001b[0;32mPAYOUT:\u001b[0m {seed['payout']}\n\n"
                        f"\u001b[0;34m[CLIENT]\u001b[0m {seed['client']}\n"
                        f"\u001b[0;34m[OBJECTIVE]\u001b[0m {seed['objective']}\n"
                        f"\u001b[0;34m[LOCATION]\u001b[0m {seed['location']}\n"
                        f"\u001b[0;34m[ADVERSARY]\u001b[0m {seed['adversary']}\n"
                        f"\u001b[0;31m[TWIST]\u001b[0m {seed['twist']}"
                    )
                    
                    embed = DiscordEmbed(
                        description=f"```ansi\n{hook_text}\n```",
                        color=get_diff_color(seed['difficulty'])
                    )
                    webhook.add_embed(embed)

                response = webhook.execute()
                if response.status_code in [200, 204]:
                    st.success("Data packets dispatched to the crew.")
                else:
                    st.error(f"Uplink failed: {response.status_code}")
            except Exception as e:
                st.error(f"CRITICAL ERROR: {str(e)}")