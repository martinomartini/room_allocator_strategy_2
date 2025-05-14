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

        # --- Team Allocation ---
        cur.execute("SELECT team_name, team_size, preferred_days FROM weekly_preferences")
        team_preferences = cur.fetchall()
        random.shuffle(team_preferences)

        used_rooms = {d: [] for d in day_mapping.values()}
        team_to_days = {}
        team_to_prefdays = {}

        for team_name, team_size, preferred_str in team_preferences:
            preferred_days = [d.strip() for d in preferred_str.split(",") if d.strip() in day_mapping]
            if len(preferred_days) != 2:
                continue
            d1, d2 = day_mapping[preferred_days[0]], day_mapping[preferred_days[1]]
            team_to_prefdays[team_name] = {d1, d2}

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

        # --- Fallback for teams with < 2 days ---
        teams_needing_more = [team for team in team_to_prefdays if len(team_to_days.get(team, [])) < 2]
        random.shuffle(teams_needing_more)

        for team_name in teams_needing_more:
            assigned = set(team_to_days.get(team_name, []))
            preferred = team_to_prefdays[team_name]
            team_size = next(size for name, size, _ in team_preferences if name == team_name)

            for date in day_mapping.values():
                if date in preferred or date in assigned:
                    continue
                available = [r for r in project_rooms if r["capacity"] >= team_size and r["name"] not in used_rooms[date]]
                if available:
                    room = random.choice(available)["name"]
                    cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)", (team_name, room, date))
                    used_rooms[date].append(room)
                    team_to_days.setdefault(team_name, []).append(date)
                    break

        # --- Oasis Allocation ---
        oasis_unplaced = []
        if oasis:
            cur.execute("SELECT person_name, preferred_days FROM oasis_preferences")
            person_rows = cur.fetchall()
            random.shuffle(person_rows)

            oasis_used = {d: set() for d in day_mapping.values()}
            person_to_days = {}
            person_to_prefdays = {}

            for person_name, preferred_str in person_rows:
                preferred_days = [d.strip() for d in preferred_str.split(",") if d.strip() in day_mapping]
                if len(preferred_days) != 2:
                    continue
                d1, d2 = day_mapping[preferred_days[0]], day_mapping[preferred_days[1]]
                person_to_prefdays[person_name] = {d1, d2}

                if len(oasis_used[d1]) < oasis["capacity"] and len(oasis_used[d2]) < oasis["capacity"]:
                    cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)", (person_name, "Oasis", d1))
                    cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)", (person_name, "Oasis", d2))
                    oasis_used[d1].add(person_name)
                    oasis_used[d2].add(person_name)
                    person_to_days[person_name] = [d1, d2]

            # Fallback for people with < 2 days
            people_needing_more = [p for p in person_to_prefdays if len(person_to_days.get(p, [])) < 2]
            random.shuffle(people_needing_more)

            for person_name in people_needing_more:
                assigned = set(person_to_days.get(person_name, []))
                preferred = person_to_prefdays[person_name]
                for date in day_mapping.values():
                    if date in preferred or date in assigned:
                        continue
                    if len(oasis_used[date]) < oasis["capacity"]:
                        cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)", (person_name, "Oasis", date))
                        oasis_used[date].add(person_name)
                        person_to_days.setdefault(person_name, []).append(date)
                        break

        conn.commit()
        cur.close()
        conn.close()

        final_unplaced_teams = sorted([t for t in team_to_prefdays if t not in team_to_days])
        final_unplaced_oasis = sorted([p for p in person_to_prefdays if p not in person_to_days])
        return True, final_unplaced_teams + final_unplaced_oasis

    except Exception as e:
        print(f"Allocation failed: {e}")
        return False, []
