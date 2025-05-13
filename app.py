import streamlit as st
import psycopg2
import psycopg2.pool
import json
import os
from datetime import datetime
import pytz
import pandas as pd
from allocate_rooms import run_allocation

# --- Configuration ---
st.set_page_config(page_title="Weekly Room Allocator", layout="centered")
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

def get_room_grid(pool):
    conn = get_connection_from_pool(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT team_name, room_name, date FROM weekly_allocations")
            data = cur.fetchall()
            if not data:
                return pd.DataFrame()
            df = pd.DataFrame(data, columns=["Team", "Room", "Date"])
            df["Date"] = pd.to_datetime(df["Date"])
            df["Day"] = df["Date"].dt.strftime('%A')
            pivot = df.pivot(index="Room", columns="Day", values="Team").fillna("Vacant")
            return pivot.reset_index()
    except Exception as e:
        st.warning(f"Failed to load allocation data: {e}")
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
        return_connection_from_pool(pool, conn)

def get_oasis_preferences(pool):
    conn = get_connection_from_pool(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT person_name, preferred_days, submission_time FROM oasis_preferences")
            rows = cur.fetchall()
            return pd.DataFrame(rows, columns=["Person", "Preferred Days", "Submitted At"])
    finally:
        return_connection_from_pool(pool, conn)

def insert_preference(pool, team_name, contact_person, team_size, preferred_days):
    if team_size > 5:
        st.error("❌ Team size cannot be larger than 5.")
        return False

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

            if not (new_days == {"Monday", "Wednesday"} or new_days == {"Tuesday", "Thursday"}):
                st.error("❌ Please select either Monday & Wednesday OR Tuesday & Thursday.")
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

def insert_oasis_preference(pool, person_name, preferred_days):
    conn = get_connection_from_pool(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO oasis_preferences (person_name, preferred_days, submission_time)
                VALUES (%s, %s, NOW())
            """, (person_name, preferred_days))
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Failed to save oasis preference: {e}")
        return False
    finally:
        return_connection_to_pool(pool, conn)

def reset_preferences(pool):
    conn = get_connection_from_pool(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM weekly_preferences")
            cur.execute("DELETE FROM oasis_preferences")
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
        return_connection_from_pool(pool, conn)

# --- UI ---
st.title("📅 Weekly Room Allocator")
now_local = datetime.now(OFFICE_TIMEZONE)
st.info(f"Current Office Time: **{now_local.strftime('%Y-%m-%d %H:%M:%S')}** ({OFFICE_TIMEZONE_STR})")

db_pool = get_db_connection_pool()

# --- Admin Panel ---
with st.expander("🔐 Admin Controls"):
    password = st.text_input("Enter admin password:", type="password")
    if password == RESET_PASSWORD:
        if st.button("🧮 Run Allocation Now"):
            if run_allocation(DATABASE_URL):
                st.success("✅ Allocations updated.")
            else:
                st.error("❌ Allocation failed. See logs.")

        if st.button("🗑️ Reset Preferences"):
            if reset_preferences(db_pool):
                st.success("✅ Preferences reset.")

        if st.button("🧼 Reset Allocations"):
            if reset_allocations(db_pool):
                st.success("✅ Allocations reset.")

        st.subheader("Team Preferences")
        team_prefs = get_preferences(db_pool)
        if not team_prefs.empty:
            st.dataframe(team_prefs, use_container_width=True)

        st.subheader("Oasis Preferences")
        oasis_prefs = get_oasis_preferences(db_pool)
        if not oasis_prefs.empty:
            st.dataframe(oasis_prefs, use_container_width=True)
    elif password:
        st.error("❌ Incorrect password.")

# --- Preference Form ---
st.header("Submit Your Preference for Next Week")
with st.form("weekly_preference_form"):
    team_name = st.text_input("Team Name:")
    contact_person = st.text_input("Contact Person:")
    team_size = st.number_input("Team Size:", min_value=1)
    selected_days = st.multiselect(
        "Select 2 preferred office days:",
        ["Monday and Wednesday", "Tuesday and Thursday"],
        max_selections=1
    )
    submitted = st.form_submit_button("Submit Preference")
    if submitted:
        if not team_name or not contact_person:
            st.warning("Please complete all fields.")
        elif len(selected_days) != 1:
            st.warning("Please select exactly one option.")
        else:
            day_map = {
                "Monday and Wednesday": "Monday,Wednesday",
                "Tuesday and Thursday": "Tuesday,Thursday"
            }
            preferred_days = day_map[selected_days[0]]
            if db_pool:
                success = insert_preference(db_pool, team_name, contact_person, team_size, preferred_days)
                if success:
                    st.success("✅ Preference submitted successfully!")

# --- Oasis Form ---
st.header("Reserve Your Oasis Seat")
with st.form("oasis_form"):
    person_name = st.text_input("Your Name:")
    selected_oasis = st.multiselect(
        "Select 2 preferred days for Oasis:",
        ["Monday and Wednesday", "Tuesday and Thursday"],
        max_selections=1
    )
    submitted_oasis = st.form_submit_button("Submit Oasis Preference")
    if submitted_oasis:
        if not person_name or not selected_oasis:
            st.warning("Please fill out all Oasis fields.")
        else:
            day_map = {
                "Monday and Wednesday": "Monday,Wednesday",
                "Tuesday and Thursday": "Tuesday,Thursday"
            }
            preferred_days = day_map[selected_oasis[0]]
            if db_pool:
                success = insert_oasis_preference(db_pool, person_name, preferred_days)
                if success:
                    st.success("✅ Oasis preference submitted!")

# --- Allocation View ---
st.header("Current Room Allocations")
if db_pool:
    grid = get_room_grid(db_pool)
    if grid.empty:
        st.write("No allocations available yet.")
    else:
        st.dataframe(grid, use_container_width=True)

st.divider()
st.caption("Manage voting and allocation directly from the admin panel above.")
