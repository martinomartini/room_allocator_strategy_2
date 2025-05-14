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
        cur.execute("DELETE FROM weekly_allocations")

        # --- Team Preferences ---
        cur.execute("SELECT team_name, team_size, preferred_days FROM weekly_preferences")
        team_preferences = cur.fetchall()

        used_rooms = {d: [] for d in day_mapping.values()}
        team_to_days = {}

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

        # --- Fallback to opposite pair if original failed ---
        placed_teams = set(team_to_days.keys())
        all_teams = {t for t, _, _ in team_preferences}
        unplaced = list(all_teams - placed_teams)

        for team_name in random.sample(unplaced, len(unplaced)):
            team_size = next(s for t, s, _ in team_preferences if t == team_name)
            preferred_str = next(p for t, _, p in team_preferences if t == team_name)
            preferred_days = sorted([d.strip() for d in preferred_str.split(",") if d.strip() in day_mapping])
            if preferred_days == ["Monday", "Wednesday"]:
                fallback_days = ["Tuesday", "Thursday"]
            elif preferred_days == ["Tuesday", "Thursday"]:
                fallback_days = ["Monday", "Wednesday"]
            else:
                continue  # skip invalid

            d1 = day_mapping[fallback_days[0]]
            d2 = day_mapping[fallback_days[1]]

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

        # --- Oasis Allocation (New Logic) ---
        cur.execute("SELECT person_name, preferred_day_1, preferred_day_2 FROM oasis_preferences")
        person_rows = cur.fetchall()
        random.shuffle(person_rows)  # Randomize order

        oasis_used = {d: set() for d in day_mapping.values()}
        person_to_days = {}

        # Round 1: Assign both preferred days if capacity allows
        for person_name, d1_label, d2_label in person_rows:
            if d1_label not in day_mapping or d2_label not in day_mapping:
                continue  # skip invalid input

            d1 = day_mapping[d1_label]
            d2 = day_mapping[d2_label]

            if len(oasis_used[d1]) < oasis["capacity"] and len(oasis_used[d2]) < oasis["capacity"]:
                cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)", (person_name, "Oasis", d1))
                cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)", (person_name, "Oasis", d2))
                oasis_used[d1].add(person_name)
                oasis_used[d2].add(person_name)
                person_to_days[person_name] = [d1, d2]

        # Round 2: Fallback for unplaced people — any two available days
        placed_people = set(person_to_days.keys())
        all_people = {p for p, _, _ in person_rows}
        unplaced_people = list(all_people - placed_people)

        for person_name in random.sample(unplaced_people, len(unplaced_people)):
            available_days = [d for d in day_mapping.values() if len(oasis_used[d]) < oasis["capacity"]]
            random.shuffle(available_days)
            if len(available_days) < 2:
                continue  # Not enough space for two days

            d1, d2 = available_days[:2]
            cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)", (person_name, "Oasis", d1))
            cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)", (person_name, "Oasis", d2))
            oasis_used[d1].add(person_name)
            oasis_used[d2].add(person_name)
            person_to_days[person_name] = [d1, d2]

        conn.commit()
        cur.close()
        conn.close()

        unplaced_teams = sorted([t for t, _, _ in team_preferences if t not in team_to_days])
        unplaced_people = sorted([p for p, _, _ in person_rows if p not in person_to_days])
        return True, unplaced_teams + unplaced_people

    except Exception as e:
        print(f"Allocation failed: {e}")
        return False, []
