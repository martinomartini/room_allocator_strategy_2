# allocate_rooms.py

import psycopg2
import json
import os
from datetime import datetime, timedelta
import pytz

# --- Time Setup ---
OFFICE_TIMEZONE = pytz.timezone("Europe/Amsterdam")
now = datetime.now(OFFICE_TIMEZONE)
this_monday = now - timedelta(days=now.weekday())
day_mapping = {
    "Monday": this_monday.date(),
    "Tuesday": (this_monday + timedelta(days=1)).date(),
    "Wednesday": (this_monday + timedelta(days=2)).date(),
    "Thursday": (this_monday + timedelta(days=3)).date(),
}

# --- Load Room Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOMS_FILE = os.path.join(BASE_DIR, "rooms.json")
with open(ROOMS_FILE, "r") as f:
    rooms = json.load(f)

project_rooms = [r for r in rooms if r["name"] != "Oasis"]
oasis = next((r for r in rooms if r["name"] == "Oasis"), None)

def run_allocation(database_url):
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()

        # Clear old allocations
        cur.execute("DELETE FROM weekly_allocations")

        # --- Team Allocation ---
        cur.execute("SELECT team_name, team_size, preferred_days FROM weekly_preferences")
        team_preferences = cur.fetchall()
        used_rooms = {d: [] for d in day_mapping.values()}

        for team_name, team_size, preferred_str in team_preferences:
            preferred_days = [d.strip() for d in preferred_str.split(",") if d.strip() in day_mapping]
            assigned_days = []

            # Try preferred days first
            for day_name in preferred_days:
                date = day_mapping[day_name]
                possible_rooms = sorted(
                    [r for r in project_rooms if r['capacity'] >= team_size and r['name'] not in used_rooms[date]],
                    key=lambda x: x['capacity']
                )
                if possible_rooms:
                    room = possible_rooms[0]['name']
                    cur.execute(
                        "INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)",
                        (team_name, room, date)
                    )
                    used_rooms[date].append(room)
                    assigned_days.append(date)
                    if len(assigned_days) >= 2:
                        break

            # Fallback to other days if fewer than 2 assigned
            if len(assigned_days) < 2:
                for fallback_day, date in day_mapping.items():
                    if date in assigned_days:
                        continue
                    possible_rooms = sorted(
                        [r for r in project_rooms if r['capacity'] >= team_size and r['name'] not in used_rooms[date]],
                        key=lambda x: x['capacity']
                    )
                    if possible_rooms:
                        room = possible_rooms[0]['name']
                        cur.execute(
                            "INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)",
                            (team_name, room, date)
                        )
                        used_rooms[date].append(room)
                        assigned_days.append(date)
                        if len(assigned_days) >= 2:
                            break

        # --- Oasis Allocation ---
        if oasis:
            oasis_used = {d: [] for d in day_mapping.values()}
            cur.execute("SELECT person_name, preferred_days FROM oasis_preferences")
            person_rows = cur.fetchall()

            for person_name, preferred_str in person_rows:
                preferred_days = [d.strip() for d in preferred_str.split(",") if d.strip() in day_mapping]
                for day_name in preferred_days:
                    date = day_mapping[day_name]
                    if len(oasis_used[date]) < oasis["capacity"]:
                        cur.execute(
                            "INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)",
                            (person_name, "Oasis", date)
                        )
                        oasis_used[date].append(person_name)

        conn.commit()
        cur.close()
        conn.close()
        return True

    except Exception as e:
        print(f"Allocation failed: {e}")
        return False
