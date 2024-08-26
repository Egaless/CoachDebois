import re
import json
import streamlit as st
import pandas as pd
from pathlib import Path

# Define the keys we are interested in
keys = ['NAME', 'SKIN', 'CHAMPION_VS', 'INDIVIDUAL_POSITION', 'TEAM', 'WIN',
        'CHAMPIONS_KILLED', 'NUM_DEATHS', 'ASSISTS', 'KDA', 'KP', 'WARD_PLACED',
        'WARD_KILLED', 'VISION_WARDS_BOUGHT_IN_GAME', 'TOTAL_WARD_ADV', 'VISION_SCORE',
        'SPELL1_CAST', 'SPELL2_CAST', 'SPELL3_CAST', 'SPELL4_CAST', 'SUMMON_SPELL1_CAST',
        'SUMMON_SPELL2_CAST', 'TOTAL_HEAL', 'CS', 'NEUTRAL_MINIONS_KILLED',
        'NEUTRAL_MINIONS_KILLED_YOUR_JUNGLE', 'NEUTRAL_MINIONS_KILLED_ENEMY_JUNGLE',
        'MINIONS_KILLED', 'TURRETS_KILLED', 'TOTAL_KILLED_TURRET_ADV', 'CS_MINUTES',
        'GOLD_EARNED', 'TEAM_GOLD', 'GOLD_POURCENTAGE', 'GOLD_MINUTE', 'ADV_GOLD_INDIV',
        'TOTAL_GOLD_ADV', 'TOTAL_DAMAGE_DEALT_TO_BUILDINGS', 'TOTAL_DAMAGE_DEALT_TO_OBJECTIVES',
        'TOTAL_DAMAGE_TAKEN', 'PHYSICAL_DAMAGE_TAKEN', 'MAGIC_DAMAGE_TAKEN',
        'TOTAL_DAMAGE_DEALT_TO_CHAMPIONS', 'MAGIC_DAMAGE_DEALT_TO_CHAMPIONS',
        'PHYSICAL_DAMAGE_DEALT_TO_CHAMPIONS', 'TEAM_DMG', 'DMG_POURCENTAGE', 'DMG_MINUTE',
        'DMG_GOLD', 'DOUBLE_KILLS', 'TRIPLE_KILLS', 'QUADRA_KILLS', 'PENTA_KILLS', 'PING',
        'PATCH', 'DUREE_GAME']

def extract_json_from_rofl(file):
    content = file.read()
    brace_stack = []
    start_idx = None
    end_idx = None

    for idx, byte in enumerate(content):
        if byte == ord('{'):
            brace_stack.append(idx)
            if start_idx is None:
                start_idx = idx
        elif byte == ord('}'):
            if brace_stack:
                brace_stack.pop()
                if not brace_stack:
                    end_idx = idx
                    break

    start_sequence = b'{"'
    start_sequence_idx = content.find(start_sequence)
    if start_sequence_idx == -1:
        st.error("Début de séquence non trouvé.")
        return None

    end_sequence = b'}]"}'
    end_sequence_idx = content.find(end_sequence, start_sequence_idx)
    if end_sequence_idx == -1:
        st.error("Fin de séquence non trouvée.")
        return None

    json_bytes = content[start_sequence_idx:end_sequence_idx + len(end_sequence)]
    try:
        json_str = json_bytes.decode('utf-8', 'ignore')
        json_object = json.loads(json_str)
        gameLength = json_object.get("gameLength", "")
        gameVersion = json_object.get("gameVersion", "")
        stats_json_data_str = json_object.get('statsJson', '[]')
        stats_json_data = json.loads(stats_json_data_str)
        return gameLength, gameVersion, stats_json_data

    except json.JSONDecodeError as e:
        st.error(f"Erreur de décodage JSON: {e}")
        return None

def milliseconds_to_hms(milliseconds, format):
    if format == "date":
        seconds = milliseconds / 1000
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return "{:02d}:{:02d}:{:02d}".format(int(hours), int(minutes), int(seconds))
    elif format == "minute":
        return milliseconds / 60000

def traitement_RED_BLUE(teamGame):
    return "RED" if teamGame == "200" else "BLUE"

def traitement_WIN_LOSE(statutGame):
    return "WIN" if statutGame == "Win" else "LOSE"

def traitement_json(data_json, keys, selected_team):
    full_participants = {"participants": []}
    
    for item in data_json:
        modified_item = {key: item.get(key, "") for key in keys}
        full_participants["participants"].append(modified_item)

    # Filter participants based on the selected team
    team_participants = {
        "participants": [p for p in full_participants["participants"] if p["TEAM"] == selected_team]
    }

    # Compute metrics for the selected team
    team_gold = sum(int(participant["GOLD_EARNED"]) for participant in team_participants["participants"])
    team_dmg = sum(int(participant["TOTAL_DAMAGE_DEALT_TO_CHAMPIONS"]) for participant in team_participants["participants"])
    kill_team = sum(int(participant["CHAMPIONS_KILLED"]) for participant in team_participants["participants"])

    for participant in team_participants["participants"]:
        participant["TEAM"] = traitement_RED_BLUE(participant["TEAM"])
        participant["WIN"] = traitement_WIN_LOSE(participant["WIN"])

        if int(participant["NUM_DEATHS"]) == 0:
            participant["KDA"] = (int(participant["CHAMPIONS_KILLED"]) + int(participant["ASSISTS"]))
        else:
            participant["KDA"] = (int(participant["CHAMPIONS_KILLED"]) + int(participant["ASSISTS"])) / int(participant["NUM_DEATHS"])

        participant["KP"] = (int(participant["CHAMPIONS_KILLED"]) + int(participant["ASSISTS"])) / kill_team if kill_team != 0 else 0
        participant["CS"] = int(participant["MINIONS_KILLED"]) + int(participant["NEUTRAL_MINIONS_KILLED"])

        participant["TEAM_GOLD"] = team_gold
        participant["GOLD_POURCENTAGE"] = int(participant["GOLD_EARNED"]) / team_gold if team_gold != 0 else 0

        participant["TEAM_DMG"] = team_dmg
        participant["DMG_GOLD"] = int(participant["TOTAL_DAMAGE_DEALT_TO_CHAMPIONS"]) / int(participant["GOLD_EARNED"]) if int(participant["GOLD_EARNED"]) != 0 else 0

    return team_participants

def process_rofl(file, selected_team):
    gameLength, gameVersion, data_participants = extract_json_from_rofl(file)
    if data_participants:
        json_game = traitement_json(data_participants, keys, selected_team)
        return pd.DataFrame(json_game["participants"])
    else:
        st.error("Le fichier n'a pas pu être traité.")
        return pd.DataFrame()

# Streamlit UI
st.title("ROFL to Game Data")
st.write("Téléchargez un fichier ROFL pour extraire et afficher les données.")

uploaded_file = st.file_uploader("Choisissez un fichier ROFL", type="rofl")

# User selection for team
team_selection = st.radio("Sélectionnez l'équipe à analyser", ('(Blue)', '(Red)'))
selected_team = '100' if 'Blue' in team_selection else '200'

if uploaded_file:
    data_df = process_rofl(uploaded_file, selected_team)
    st.dataframe(data_df)
