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

        # Clear old allocations
        cur.execute("DELETE FROM weekly_allocations")

        # --- Load Team Preferences ---
        cur.execute("SELECT team_name, team_size, preferred_days FROM weekly_preferences")
        team_preferences = cur.fetchall()
        random.shuffle(team_preferences)

        used_rooms = {d: [] for d in day_mapping.values()}
        team_to_days = {}
        all_team_names = {team_name for team_name, _, _ in team_preferences}

        # --- First round: place each team once on preferred days ---
        for team_name, team_size, preferred_str in team_preferences:
            preferred_days = [d.strip() for d in preferred_str.split(",") if d.strip() in day_mapping]
            random.shuffle(preferred_days)
            for day in preferred_days:
                date = day_mapping[day]
                available = [r for r in project_rooms if r["capacity"] >= team_size and r["name"] not in used_rooms[date]]
                if available:
                    room = random.choice(available)["name"]
                    cur.execute(
                        "INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)",
                        (team_name, room, date)
                    )
                    used_rooms[date].append(room)
                    team_to_days.setdefault(team_name, []).append(date)
                    break

        # --- Second round: try to add second preferred day for teams ---
        for team_name, team_size, preferred_str in team_preferences:
            preferred_days = [d.strip() for d in preferred_str.split(",") if d.strip() in day_mapping]
            random.shuffle(preferred_days)
            for day in preferred_days:
                date = day_mapping[day]
                if date in team_to_days.get(team_name, []):
                    continue
                available = [r for r in project_rooms if r["capacity"] >= team_size and r["name"] not in used_rooms[date]]
                if available:
                    room = random.choice(available)["name"]
                    cur.execute(
                        "INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)",
                        (team_name, room, date)
                    )
                    used_rooms[date].append(room)
                    team_to_days.setdefault(team_name, []).append(date)

        # --- Third round: fallback for teams with fewer than 2 placements on any day ---
        teams_needing_more = [team_name for team_name in all_team_names if len(team_to_days.get(team_name, [])) < 2]
        random.shuffle(teams_needing_more)
        for team_name in teams_needing_more:
            team_size = next(size for name, size, _ in team_preferences if name == team_name)
            for day, date in day_mapping.items():
                if date in team_to_days.get(team_name, []):
                    continue
                available = [r for r in project_rooms if r["capacity"] >= team_size and r["name"] not in used_rooms[date]]
                if available:
                    room = random.choice(available)["name"]
                    cur.execute(
                        "INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)",
                        (team_name, room, date)
                    )
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

            # First round: place once on preferred days
            for person_name, preferred_str in person_rows:
                preferred_days = [d.strip() for d in preferred_str.split(",") if d.strip() in day_mapping]
                random.shuffle(preferred_days)
                for day in preferred_days:
                    date = day_mapping[day]
                    if len(oasis_used[date]) < oasis["capacity"]:
                        cur.execute(
                            "INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)",
                            (person_name, "Oasis", date)
                        )
                        oasis_used[date].add(person_name)
                        person_to_days.setdefault(person_name, []).append(date)
                        break

            # Second round: second preferred day
            for person_name, preferred_str in person_rows:
                preferred_days = [d.strip() for d in preferred_str.split(",") if d.strip() in day_mapping]
                random.shuffle(preferred_days)
                for day in preferred_days:
                    date = day_mapping[day]
                    if date in person_to_days.get(person_name, []):
                        continue
                    if len(oasis_used[date]) < oasis["capacity"]:
                        cur.execute(
                            "INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)",
                            (person_name, "Oasis", date)
                        )
                        oasis_used[date].add(person_name)
                        person_to_days.setdefault(person_name, []).append(date)

            # Third round: fallback for people with <2 placements on any free day
            people_needing_more = [p for p in [row[0] for row in person_rows] if len(person_to_days.get(p, [])) < 2]
            random.shuffle(people_needing_more)
            for person_name in people_needing_more:
                for day, date in day_mapping.items():
                    if date in person_to_days.get(person_name, []):
                        continue
                    if len(oasis_used[date]) < oasis["capacity"]:
                        cur.execute(
                            "INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)",
                            (person_name, "Oasis", date)
                        )
                        oasis_used[date].add(person_name)
                        person_to_days.setdefault(person_name, []).append(date)
                        break

            # Final unplaced Oasis users = those with 0 days
            oasis_unplaced = [p for p in [row[0] for row in person_rows] if p not in person_to_days]

        conn.commit()
        cur.close()
        conn.close()

        unplaced_teams = sorted([t for t in all_team_names if len(team_to_days.get(t, [])) == 0])
        return True, sorted(unplaced_teams + oasis_unplaced)

    except Exception as e:
        print(f"Allocation failed: {e}")
        return False, []
