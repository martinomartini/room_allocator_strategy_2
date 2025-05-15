import psycopg2
import json
import os
from datetime import datetime, timedelta
import pytz
import random

# --- Time Setup ---
OFFICE_TIMEZONE = pytz.timezone("Europe/Amsterdam")
now = datetime.now(OFFICE_TIMEZONE)
this_monday = now - timedelta(days=now.weekday())
day_mapping = {
    "Monday": this_monday.date(),
    "Tuesday": (this_monday + timedelta(days=1)).date(),
    "Wednesday": (this_monday + timedelta(days=2)).date(),
    "Thursday": (this_monday + timedelta(days=3)).date(),
    "Friday": (this_monday + timedelta(days=4)).date(),
}

# --- Load Room Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOMS_FILE = os.path.join(BASE_DIR, "rooms.json")
with open(ROOMS_FILE, "r") as f:
    rooms = json.load(f)

project_rooms = [r for r in rooms if r["name"] != "Oasis"]
oasis = next((r for r in rooms if r["name"] == "Oasis"), None)

# --- Main Allocation ---
def run_allocation(database_url, only=None):
    import psycopg2
    import random

    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor()
        cur.execute("DELETE FROM weekly_allocations")

        team_to_days = {}
        person_to_days = {}

        if only in [None, "project"]:
            # --- Project Room Allocation ---
            cur.execute("SELECT team_name, team_size, preferred_days FROM weekly_preferences")
            team_preferences = cur.fetchall()

            used_rooms = {d: [] for d in day_mapping.values()}

            mon_wed = []
            tue_thu = []

            for team_name, team_size, preferred_str in team_preferences:
                preferred_days = sorted([d.strip() for d in preferred_str.split(",") if d.strip() in day_mapping])
                if preferred_days == ["Monday", "Wednesday"]:
                    mon_wed.append((team_name, team_size, preferred_days))
                elif preferred_days == ["Tuesday", "Thursday"]:
                    tue_thu.append((team_name, team_size, preferred_days))

            def assign_combo(group, d1_label, d2_label):
                d1 = day_mapping[d1_label]
                d2 = day_mapping[d2_label]
                for team_name, team_size, _ in random.sample(group, len(group)):
                    available_d1 = [r for r in project_rooms if r["capacity"] >= team_size and r["name"] not in used_rooms[d1]]
                    available_d2 = [r for r in project_rooms if r["capacity"] >= team_size and r["name"] not in used_rooms[d2]]
                    if available_d1 and available_d2:
                        room1 = random.choice(available_d1)["name"]
                        room2 = random.choice(available_d2)["name"]
                        cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)", (team_name, room1, d1))
                        cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)", (team_name, room2, d2))
                        used_rooms[d1].append(room1)
                        used_rooms[d2].append(room2)
                        team_to_days[team_name] = [d1, d2]

            assign_combo(mon_wed, "Monday", "Wednesday")
            assign_combo(tue_thu, "Tuesday", "Thursday")

            # --- Fallback ---
            placed_teams = set(team_to_days.keys())
            all_teams = {t for t, _, _ in team_preferences}
            unplaced = list(all_teams - placed_teams)

            for team_name in random.sample(unplaced, len(unplaced)):
                team_size = next(s for t, s, _ in team_preferences if t == team_name)
                preferred_str = next(p for t, _, p in team_preferences if t == team_name)
                preferred_days = sorted([d.strip() for d in preferred_str.split(",") if d.strip() in day_mapping])
                fallback = ["Tuesday", "Thursday"] if preferred_days == ["Monday", "Wednesday"] else ["Monday", "Wednesday"]

                d1 = day_mapping[fallback[0]]
                d2 = day_mapping[fallback[1]]
                available_d1 = [r for r in project_rooms if r["capacity"] >= team_size and r["name"] not in used_rooms[d1]]
                available_d2 = [r for r in project_rooms if r["capacity"] >= team_size and r["name"] not in used_rooms[d2]]

                if available_d1 and available_d2:
                    room1 = random.choice(available_d1)["name"]
                    room2 = random.choice(available_d2)["name"]
                    cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)", (team_name, room1, d1))
                    cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)", (team_name, room2, d2))
                    used_rooms[d1].append(room1)
                    used_rooms[d2].append(room2)
                    team_to_days[team_name] = [d1, d2]

        if only in [None, "oasis"]:
            # --- Oasis Allocation (5-day logic) ---
            cur.execute("SELECT person_name, preferred_day_1, preferred_day_2, preferred_day_3, preferred_day_4, preferred_day_5 FROM oasis_preferences")
            person_rows = cur.fetchall()
            random.shuffle(person_rows)

            oasis_used = {d: set() for d in day_mapping.values()}
            person_prefs = {
                name: [d for d in [d1, d2, d3, d4, d5] if d and d in day_mapping]
                for name, d1, d2, d3, d4, d5 in person_rows
            }

            # Round 1: Give everyone one preferred day
            for name, prefs in person_prefs.items():
                for day in prefs:
                    date = day_mapping[day]
                    if len(oasis_used[date]) < oasis["capacity"]:
                        cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, 'Oasis', %s)", (name, date))
                        oasis_used[date].add(name)
                        person_to_days[name] = [date]
                        break

            # Round 2: Give more preferred days if room available
            for name, prefs in person_prefs.items():
                for day in prefs:
                    date = day_mapping[day]
                    if name not in oasis_used[date] and len(oasis_used[date]) < oasis["capacity"]:
                        cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, 'Oasis', %s)", (name, date))
                        oasis_used[date].add(name)
                        person_to_days.setdefault(name, []).append(date)

        conn.commit()
        cur.close()
        conn.close()
        return True, []

    except Exception as e:
        print(f"Allocation failed: {e}")
        return False, []
