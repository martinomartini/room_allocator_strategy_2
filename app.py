import streamlit as st
import psycopg2
import psycopg2.pool
import json
import os
from datetime import datetime
import pytz
import pandas as pd

# --- Configuration ---
DATABASE_URL = st.secrets.get("SUPABASE_DB_URI", os.environ.get("SUPABASE_DB_URI"))
OFFICE_TIMEZONE_STR = st.secrets.get("OFFICE_TIMEZONE", os.environ.get("OFFICE_TIMEZONE", "UTC"))
RESET_PASSWORD = "trainee"

try:
    OFFICE_TIMEZONE = pytz.timezone(OFFICE_TIMEZONE_STR)
except pytz.UnknownTimeZoneError:
    st.error(f"Invalid Timezone: '{OFFICE_TIMEZONE_STR}', defaulting to UTC.")
    OFFICE_TIMEZONE = pytz.utc

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOMS_FILE = os.path.join(BASE_DIR, 'rooms.json')

try:
    with open(ROOMS_FILE, 'r') as f:
        AVAILABLE_ROOMS = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    st.error("Room configuration file is missing or invalid.")
    st.stop()

# --- Database Helpers ---
@st.cache_resource
def get_db_connection_pool():
    if not DATABASE_URL:
        st.error("Missing SUPABASE_DB_URI.")
        return None
    try:
        return psycopg2.pool.SimpleConnectionPool(1, 5, dsn=DATABASE_URL)
    except Exception as e:
        st.error(f"Database connection pool error: {e}")
        return None

def get_connection_from_pool(pool):
    try:
        return pool.getconn()
    except:
        return None

def return_connection_to_pool(pool, conn):
    try:
        pool.putconn(conn)
    except:
        pass

def insert_preference(pool, team_name, contact_person, team_size, preferred_days):
    conn = get_connection_from_pool(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT preferred_days FROM weekly_preferences
                WHERE team_name = %s
            """, (team_name,))
            existing_days = cur.fetchall()
            submitted_days = set()
            for row in existing_days:
                submitted_days.update(row[0].split(','))

            new_days = set(preferred_days.split(','))
            combined = submitted_days.union(new_days)

            if len(submitted_days) >= 2:
                st.error("❌ This team has already submitted preferences for 2 days.")
                return False
            if len(combined) > 2:
                st.error("❌ Submitting these days would exceed the 2-day limit per team.")
                return False

            cur.execute("""
                INSERT INTO weekly_preferences (team_name, contact_person, team_size, preferred_days, submission_time)
                VALUES (%s, %s, %s, %s, NOW())
            """, (team_name, contact_person, team_size, preferred_days))
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Failed to save preference: {e}")
        return False
    finally:
        return_connection_to_pool(pool, conn)

def get_allocations(pool):
    conn = get_connection_from_pool(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT team_name, room_name, date
                FROM weekly_allocations
                ORDER BY date, room_name
            """)
            data = cur.fetchall()
            return pd.DataFrame(data, columns=["Team", "Room", "Date"])
    except Exception as e:
        st.warning("Failed to load allocation data.")
        return pd.DataFrame()
    finally:
        return_connection_to_pool(pool, conn)

def get_preferences(pool):
    conn = get_connection_from_pool(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT team_name, contact_person, team_size, preferred_days FROM weekly_preferences")
            rows = cur.fetchall()
            return pd.DataFrame(rows, columns=["Team", "Contact", "Size", "Days"])
    finally:
        return_connection_to_pool(pool, conn)

def reset_preferences(pool):
    conn = get_connection_from_pool(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM weekly_preferences")
            conn.commit()
            return True
    finally:
        return_connection_to_pool(pool, conn)

def reset_allocations(pool):
    conn = get_connection_from_pool(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM weekly_allocations")
            conn.commit()
            return True
    finally:
        return_connection_to_pool(pool, conn)

def run_allocation(pool):
    from datetime import timedelta

    OFFICE_TIMEZONE = pytz.timezone(OFFICE_TIMEZONE_STR)
    now = datetime.now(OFFICE_TIMEZONE)
    this_monday = now - timedelta(days=now.weekday())
    day_mapping = {
        "Monday": this_monday.date(),
        "Tuesday": (this_monday + timedelta(days=1)).date(),
        "Wednesday": (this_monday + timedelta(days=2)).date(),
        "Thursday": (this_monday + timedelta(days=3)).date(),
    }

    conn = get_connection_from_pool(pool)
    cur = conn.cursor()

    cur.execute("DELETE FROM weekly_allocations")
    cur.execute("SELECT team_name, team_size, preferred_days FROM weekly_preferences")
    preferences = cur.fetchall()
    used_rooms = {d: [] for d in day_mapping.values()}

    for team_name, team_size, preferred_str in preferences:
        preferred_days = [d.strip() for d in preferred_str.split(",") if d.strip() in day_mapping]
        assigned_days = []
        is_project = team_size >= 3

        for day_name in preferred_days:
            date = day_mapping[day_name]
            if is_project:
                possible = sorted(
                    [r for r in AVAILABLE_ROOMS if r['name'] != 'Oasis' and r['capacity'] >= team_size and r['name'] not in used_rooms[date]],
                    key=lambda x: x['capacity']
                )
                if possible:
                    room = possible[0]['name']
                    cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)",
                                (team_name, room, date))
                    used_rooms[date].append(room)
                    assigned_days.append(date)
            else:
                oasis = next((r for r in AVAILABLE_ROOMS if r['name'] == 'Oasis'), None)
                if oasis and used_rooms[date].count('Oasis') < oasis['capacity']:
                    cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)",
                                (team_name, 'Oasis', date))
                    used_rooms[date].append('Oasis')
                    assigned_days.append(date)

    conn.commit()
    cur.close()
    return_connection_to_pool(pool, conn)

# --- Streamlit UI ---
st.set_page_config(page_title="Weekly Room Allocator", layout="centered")
st.title("📅 Weekly Room Allocator")
now_local = datetime.now(OFFICE_TIMEZONE)
st.info(f"Current Office Time: **{now_local.strftime('%Y-%m-%d %H:%M:%S')}** ({OFFICE_TIMEZONE_STR})")

db_pool = get_db_connection_pool()

# --- Admin Panel ---
with st.expander("🔐 Admin Controls"):
    password = st.text_input("Enter admin password:", type="password")
    if password == RESET_PASSWORD:
        if st.button("🧮 Run Allocation Now"):
            run_allocation(db_pool)
            st.success("✅ Allocation completed.")

        if st.button("🗑️ Reset Preferences"):
            reset_preferences(db_pool)
            st.success("✅ Preferences reset.")

        if st.button("🧼 Reset Allocations"):
            reset_allocations(db_pool)
            st.success("✅ Allocations reset.")

        prefs_df = get_preferences(db_pool)
        if prefs_df.empty:
            st.write("No submitted preferences.")
        else:
            st.write("### Submitted Preferences")
            st.dataframe(prefs_df, use_container_width=True)
    elif password:
        st.error("❌ Incorrect password.")

# --- Display Allocations ---
st.header("Current Room Allocations")
if db_pool:
    df = get_allocations(db_pool)
    if df.empty:
        st.write("No allocations available yet.")
    else:
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime('%A %Y-%m-%d')
        st.dataframe(df, use_container_width=True)

st.divider()
st.caption("Manage voting and allocation directly from the admin panel above.")
