import psycopg2
import os
import json
from datetime import datetime, timedelta
import pytz

# --- Configuration ---
DATABASE_URL = os.environ.get("DATABASE_URL")
OFFICE_TIMEZONE_STR = os.environ.get("OFFICE_TIMEZONE", "Europe/Amsterdam")
ROOMS_FILE = os.path.join(os.path.dirname(__file__), "rooms.json")

# --- Time Setup ---
OFFICE_TIMEZONE = pytz.timezone(OFFICE_TIMEZONE_STR)
now = datetime.now(OFFICE_TIMEZONE)
this_monday = now - timedelta(days=now.weekday())
day_mapping = {
    "Monday": this_monday.date(),
    "Tuesday": (this_monday + timedelta(days=1)).date(),
    "Wednesday": (this_monday + timedelta(days=2)).date(),
    "Thursday": (this_monday + timedelta(days=3)).date(),
}

# --- Load Room Setup ---
with open(ROOMS_FILE, 'r') as f:
    rooms = json.load(f)

project_rooms = [r for r in rooms if r['name'] != 'Oasis']
oasis = next((r for r in rooms if r['name'] == 'Oasis'), None)

# --- Allocation Logic ---
def run_allocation():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Clear old allocations
    cur.execute("DELETE FROM weekly_allocations")

    # Fetch team preferences
    cur.execute("SELECT team_name, team_size, preferred_days FROM weekly_preferences")
    preferences = cur.fetchall()

    used_rooms = {d: [] for d in day_mapping.values()}
    for team_name, team_size, preferred_str in preferences:
        preferred_days = [d.strip() for d in preferred_str.split(",") if d.strip() in day_mapping]
        assigned_days = []

        for day_name in preferred_days:
            date = day_mapping[day_name]
            possible_rooms = sorted(
                [r for r in project_rooms if r['capacity'] >= team_size and r['name'] not in used_rooms[date]],
                key=lambda x: x['capacity']
            )
            if possible_rooms:
                room = possible_rooms[0]['name']
                cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)",
                            (team_name, room, date))
                used_rooms[date].append(room)
                assigned_days.append(date)

    # --- Oasis Allocation ---
    if oasis:
        cur.execute("SELECT person_name, preferred_days FROM oasis_preferences")
        individuals = cur.fetchall()

        used_oasis = {d: [] for d in day_mapping.values()}
        for person_name, preferred_str in individuals:
            preferred_days = [d.strip() for d in preferred_str.split(",") if d.strip() in day_mapping]
            for day_name in preferred_days:
                date = day_mapping[day_name]
                if used_oasis[date].count('Oasis') < oasis['capacity']:
                    cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)",
                                (person_name, 'Oasis', date))
                    used_oasis[date].append('Oasis')

    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    run_allocation()
