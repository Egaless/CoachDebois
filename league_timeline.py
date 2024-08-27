import streamlit as st
import requests
import pandas as pd




import pandas as pd


# Define the function to get match data based on match_id
def get_match(match_id,api_key="RGAPI-d4d8c650-fc42-4567-b415-46520bb879d7"):
    # Assuming there's an API endpoint or method to get the match data
    # Replace 'API_ENDPOINT' with the actual endpoint
    response = requests.get(f'https://europe.api.riotgames.com/lol/match/v5/matches/EUW1_{match_id}/timeline?api_key={api_key}')
    if response.status_code == 200:
        #print(response)
        return response.json()
    else:
        st.error("Error fetching match data. Please check the match ID.")
        return None


def create_timeline(match_dict):
    # Initialize lists to hold the extracted information
    times = []
    sides = []
    players = []
    actions = []
    targets = []
    assists = []
    bounties = []
    shutdownboutnies = []

    # List of event types we're interested in
    type_list = ['BUILDING_KILL', 'CHAMPION_KILL', 'CHAMPION_SPECIAL_KILL', 'ELITE_MONSTER_KILL', 'GAME_END', 'TURRET_PLATE_DESTROYED'] 

    # Loop over frames and then over events in each frame
    for frame in match_dict["info"]["frames"]:
        for event in frame['events']:
            event_type = event.get('type', "") 
            if event_type in type_list:
                
                # Handle CHAMPION_KILL events
                if event_type == "CHAMPION_KILL":
                    print(event)
                    times.append(event.get('timestamp', ''))
                    sides.append(event.get('killerTeamId', ''))
                    players.append(event.get('killerId', ''))
                    actions.append("KILL")
                    targets.append(event.get('victimId', ''))
                    assists.append(event.get('assistingParticipantIds', []))
                    bounties.append(event.get('bounty', ''))
                    shutdownboutnies.append(event.get('shutdownBounty',''))
                    
                elif event_type == "BUILDING_KILL":
                    times.append(event.get('timestamp', ''))
                    sides.append(event.get('teamId', ''))
                    players.append(event.get('killerId', ''))
                    actions.append("BUILDING_KILL")
                    targets.append(event.get('buildingType', '') + " " + event.get('laneType', ''))
                    assists.append(event.get('assistingParticipantIds', []))
                    bounties.append(event.get('bounty', ''))
                    shutdownboutnies.append(event.get('shutdownBounty',''))

                # Handle ELITE_MONSTER_KILL events
                elif event_type == "ELITE_MONSTER_KILL":
                    times.append(event.get('timestamp', ''))
                    sides.append(event.get('killerTeamId', ''))
                    players.append(event.get('killerId', ''))
                    actions.append("ELITE_MONSTER_KILL")
                    targets.append(event.get('monsterType', ''))
                    assists.append(event.get('assistingParticipantIds', []))
                    bounties.append(event.get('bounty', ''))
                    shutdownboutnies.append(event.get('shutdownBounty',''))

                # Handle TURRET_PLATE_DESTROYED events
                elif event_type == "TURRET_PLATE_DESTROYED":
                    times.append(event.get('timestamp', ''))
                    sides.append("")  # No side information in this event
                    players.append(event.get('killerId', ''))
                    actions.append("TURRET_PLATE_DESTROYED")
                    targets.append(event.get('laneType', ''))
                    assists.append([])  # No assists for turret plates
                    bounties.append(event.get('bounty', ''))
                    shutdownboutnies.append(event.get('shutdownBounty',''))
                    
                # Handle GAME_END events
                elif event_type == "GAME_END":
                    times.append(event.get('timestamp', ''))
                    sides.append("")  # No side for GAME_END
                    players.append("")  # No player involved directly in GAME_END
                    actions.append("GAME_END")
                    targets.append("VICTORY" if event.get('winningTeam', '') else "DEFEAT")
                    assists.append([])  # No assists in GAME_END
                    bounties.append('')  # No bounty in GAME_END
                    shutdownboutnies.append(event.get('shutdownBounty',''))

    # Create a DataFrame from the lists
    df = pd.DataFrame({
        'TIME': times,
        'SIDE': sides,
        'PLAYER': players,
        'ACTION': actions,
        'TARGET': targets,
        'ASSISTS': assists,
        'BOUNTY': bounties,
        'SHUTDOWNBOUNTY0' : shutdownboutnies 
    })

    # Convert timestamp to readable time (optional, depends on your needs)
    df['TIME'] = df['TIME'].apply(lambda x: convert_timestamp(x))
    
    return df

def convert_timestamp(timestamp):
    # Convert milliseconds to MM:SS format
    minutes = timestamp // 60000
    seconds = (timestamp % 60000) // 1000
    return f"{minutes}:{seconds:02d}"

# Streamlit App
st.title("League of Legends Match Timeline Viewer")

match_id = st.text_input("Enter Match ID:")

if match_id:
    match_data = get_match(match_id)
    
    if match_data:
        timeline_df = create_timeline(match_data)
        st.write("### Timeline of Events")
        st.dataframe(timeline_df)
