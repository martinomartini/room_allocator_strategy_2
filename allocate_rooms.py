import psycopg2
import json
import os
from datetime import datetime
from collections import defaultdict

# --- Load available rooms ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOMS_FILE = os.path.join(BASE_DIR, 'rooms.json')
with open(ROOMS_FILE, 'r') as f:
    AVAILABLE_ROOMS = json.load(f)

def run_allocation(database_url):
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()

        # Step 1: Clear existing allocations
        cur.execute("DELETE FROM weekly_allocations")

        # Step 2: Load team preferences
        cur.execute("SELECT team_name, team_size, preferred_days FROM weekly_preferences")
        rows = cur.fetchall()
        teams = []
        for team_name, size, preferred_days in rows:
            days = preferred_days.split(',')
            teams.append({
                "name": team_name,
                "size": size,
                "preferred_days": days
            })

        # Step 3: Build room availability map
        room_capacity = {room['name']: room['capacity'] for room in AVAILABLE_ROOMS if room['name'] != "Oasis"}
        room_days = ["Monday", "Tuesday", "Wednesday", "Thursday"]
        allocations = defaultdict(lambda: defaultdict(list))  # room -> day -> teams
        room_usage = defaultdict(lambda: defaultdict(int))    # room -> day -> used seats

        unplaced_teams = []

        # Step 4: Try to allocate teams
        for team in teams:
            placed = False
            for day in team["preferred_days"]:
                for room, cap in room_capacity.items():
                    if room_usage[room][day] + team["size"] <= cap:
                        allocations[room][day].append(team["name"])
                        room_usage[room][day] += team["size"]
                        placed = True
                        # Save to DB
                        cur.execute("""
                            INSERT INTO weekly_allocations (team_name, room_name, date)
                            VALUES (%s, %s, %s)
                        """, (
                            team["name"],
                            room,
                            get_upcoming_date(day)
                        ))
                        break
                if placed:
                    break
            if not placed:
                unplaced_teams.append(team["name"])

        conn.commit()
        cur.close()
        conn.close()
        return True, unplaced_teams

    except Exception as e:
        print("Allocation error:", e)
        return False, []

def get_upcoming_date(weekday_name):
    from datetime import timedelta
    today = datetime.today()
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    target_idx = weekdays.index(weekday_name)
    current_idx = today.weekday()
    delta_days = (target_idx - current_idx + 7) % 7
    if delta_days == 0:
        delta_days = 7  # always schedule to *next* instance of day
    return (today + timedelta(days=delta_days)).date()
