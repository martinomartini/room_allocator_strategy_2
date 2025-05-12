# allocate_rooms.py
import psycopg2
import os
import json
from datetime import datetime, timedelta
import pytz
import random

# --- Configuration ---
DATABASE_URL = os.environ.get("SUPABASE_DB_URI")
OFFICE_TIMEZONE_STR = os.environ.get("OFFICE_TIMEZONE", "Europe/Amsterdam")
ROOMS_FILE = os.path.join(os.path.dirname(__file__), "rooms.json")

# --- Time Setup ---
OFFICE_TIMEZONE = pytz.timezone(OFFICE_TIMEZONE_STR)

# Determine upcoming Monday
now = datetime.now(OFFICE_TIMEZONE)
upcoming_monday = now + timedelta(days=(7 - now.weekday()))
mon_wed_dates = [upcoming_monday.date(), (upcoming_monday + timedelta(days=2)).date()]
tue_thu_dates = [(upcoming_monday + timedelta(days=1)).date(), (upcoming_monday + timedelta(days=3)).date()]

# --- Load Room Setup ---
with open(ROOMS_FILE, 'r') as f:
    rooms = json.load(f)
project_rooms = [r for r in rooms if r['name'] != 'Oasis']
oasis = next((r for r in rooms if r['name'] == 'Oasis'), None)

# --- Fetch preferences and allocate ---
def run_allocation():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Clear old allocations
    cur.execute("DELETE FROM weekly_allocations")

    # Fetch preferences
    cur.execute("SELECT team_name, team_size, preferred_days FROM weekly_preferences")
    preferences = cur.fetchall()

    # Group preferences
    mon_wed = [p for p in preferences if p[2] == 'Mon + Wed']
    tue_thu = [p for p in preferences if p[2] == 'Tue + Thu']

    def allocate(pref_group, preferred_dates, fallback_dates):
        random.shuffle(pref_group)
        used_rooms = {d: [] for d in preferred_dates + fallback_dates}

        for team_name, team_size, _ in pref_group:
            is_project = team_size >= 3
            assigned_days = []

            for day in preferred_dates:
                assigned = False
                if is_project:
                    possible_rooms = sorted([r for r in project_rooms if r['capacity'] >= team_size and r['name'] not in used_rooms[day]], key=lambda x: x['capacity'])
                    if possible_rooms:
                        room = possible_rooms[0]['name']
                        cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)", (team_name, room, day))
                        used_rooms[day].append(room)
                        assigned_days.append(day)
                        assigned = True
                else:
                    if oasis and used_rooms[day].count('Oasis') < oasis['capacity']:
                        cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)", (team_name, 'Oasis', day))
                        used_rooms[day].append('Oasis')
                        assigned_days.append(day)
                        assigned = True

            # Fallback allocation if not assigned all preferred days
            while len(assigned_days) < 2:
                fallback_needed = [d for d in fallback_dates if d not in assigned_days]
                for fallback_day in fallback_needed:
                    if is_project:
                        possible_rooms = sorted([r for r in project_rooms if r['capacity'] >= team_size and r['name'] not in used_rooms[fallback_day]], key=lambda x: x['capacity'])
                        if possible_rooms:
                            room = possible_rooms[0]['name']
                            cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)", (team_name, room, fallback_day))
                            used_rooms[fallback_day].append(room)
                            assigned_days.append(fallback_day)
                            break
                    else:
                        if oasis and used_rooms[fallback_day].count('Oasis') < oasis['capacity']:
                            cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)", (team_name, 'Oasis', fallback_day))
                            used_rooms[fallback_day].append('Oasis')
                            assigned_days.append(fallback_day)
                            break

    allocate(mon_wed, mon_wed_dates, tue_thu_dates)
    allocate(tue_thu, tue_thu_dates, mon_wed_dates)

    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    run_allocation()
