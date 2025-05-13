# Full allocate_rooms.py with history-clearing logic

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
    print("🔌 Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    print("🧹 Clearing old allocations and preferences...")
    cur.execute("DELETE FROM weekly_allocations")
    cur.execute("DELETE FROM weekly_preferences")

    print("📥 Fetching team preferences (none expected after delete)...")
    cur.execute("SELECT team_name, team_size, preferred_days FROM weekly_preferences")
    preferences = cur.fetchall()
    print(f"🧠 Loaded {len(preferences)} team preferences.")

    used_rooms = {d: [] for d in day_mapping.values()}

    for team_name, team_size, preferred_str in preferences:
        print(f"\n📌 Team: {team_name} (size {team_size})")
        preferred_days = [d.strip() for d in preferred_str.split(",") if d.strip() in day_mapping]
        assigned_days = []
        is_project = team_size >= 3

        # First pass: preferred days
        for day_name in preferred_days:
            date = day_mapping[day_name]
            if is_project:
                possible = sorted(
                    [r for r in project_rooms if r['capacity'] >= team_size and r['name'] not in used_rooms[date]],
                    key=lambda x: x['capacity']
                )
                if possible:
                    room = possible[0]['name']
                    cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)",
                                (team_name, room, date))
                    used_rooms[date].append(room)
                    assigned_days.append(date)
                    print(f"✅ Assigned to {room} on {day_name}")
            else:
                if oasis and used_rooms[date].count('Oasis') < oasis['capacity']:
                    cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)",
                                (team_name, 'Oasis', date))
                    used_rooms[date].append('Oasis')
                    assigned_days.append(date)
                    print(f"✅ Assigned to Oasis on {day_name}")

        # Fallback pass
        if len(assigned_days) < 2:
            print("🔄 Applying fallback...")
        for day_name, date in day_mapping.items():
            if len(assigned_days) >= 2 or date in assigned_days:
                continue
            if is_project:
                possible = sorted(
                    [r for r in project_rooms if r['capacity'] >= team_size and r['name'] not in used_rooms[date]],
                    key=lambda x: x['capacity']
                )
                if possible:
                    room = possible[0]['name']
                    cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)",
                                (team_name, room, date))
                    used_rooms[date].append(room)
                    assigned_days.append(date)
                    print(f"➕ Fallback: {room} on {day_name}")
            else:
                if oasis and used_rooms[date].count('Oasis') < oasis['capacity']:
                    cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)",
                                (team_name, 'Oasis', date))
                    used_rooms[date].append('Oasis')
                    assigned_days.append(date)
                    print(f"➕ Fallback: Oasis on {day_name}")

    print("\n💾 Committing to database...")
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Allocation completed successfully.")

if __name__ == "__main__":
    run_allocation()
