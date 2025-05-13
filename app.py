import streamlit as st
import psycopg2
import psycopg2.pool
import pandas as pd
import json
import os
from datetime import datetime
import pytz

# --- Config ---
DATABASE_URL = st.secrets["SUPABASE_DB_URI"]
OFFICE_TIMEZONE_STR = st.secrets.get("OFFICE_TIMEZONE", "Europe/Amsterdam")
ADMIN_PASSWORD = "trainee"

try:
    OFFICE_TIMEZONE = pytz.timezone(OFFICE_TIMEZONE_STR)
except:
    OFFICE_TIMEZONE = pytz.utc

# --- Load Room File ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOMS_FILE = os.path.join(BASE_DIR, 'rooms.json')
try:
    with open(ROOMS_FILE, 'r') as f:
        AVAILABLE_ROOMS = json.load(f)
except Exception as e:
    st.error("Room configuration file is missing or invalid.")
    st.stop()

# --- DB Connection Pool ---
@st.cache_resource
def get_pool():
    return psycopg2.pool.SimpleConnectionPool(1, 5, dsn=DATABASE_URL)

pool = get_pool()

def run_query(query, params=None, fetch=False):
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            if fetch:
                result = cur.fetchall()
                return result
            conn.commit()
    finally:
        pool.putconn(conn)

def insert_preference(team_name, contact_person, team_size, preferred_days):
    if team_size > 5:
        st.error("❌ Maximum team size is 5 people.")
        return False

    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT preferred_days FROM weekly_preferences WHERE team_name = %s", (team_name,))
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
        pool.putconn(conn)

def insert_oasis_preference(name, preferred_days):
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO oasis_preferences (person_name, preferred_days, submission_time)
                VALUES (%s, %s, NOW())
            """, (name, preferred_days))
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Failed to save oasis preference: {e}")
        return False
    finally:
        pool.putconn(conn)

# --- Streamlit UI ---
st.set_page_config("Weekly Room Allocator")
st.title("📅 Weekly Room Allocator")

now = datetime.now(OFFICE_TIMEZONE)
st.info(f"Current Office Time: **{now.strftime('%Y-%m-%d %H:%M:%S')}** ({OFFICE_TIMEZONE_STR})")

# --- Admin Panel ---
with st.expander("🔐 Admin Controls"):
    pw = st.text_input("Enter admin password:", type="password")
    if pw == ADMIN_PASSWORD:
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button(":rocket: Run Allocation Now"):
                os.system("python allocate_rooms.py")
                st.success("Allocations updated.")

        with col2:
            if st.button(":wastebasket: Reset Preferences"):
                run_query("DELETE FROM weekly_preferences")
                run_query("DELETE FROM oasis_preferences")
                st.success("All preferences cleared.")

        with col3:
            if st.button(":cherry_blossom: Reset Allocations"):
                run_query("DELETE FROM weekly_allocations")
                st.success("All allocations cleared.")

        prefs = run_query("SELECT team_name, contact_person, team_size, preferred_days FROM weekly_preferences ORDER BY submission_time DESC", fetch=True)
        if prefs:
            df = pd.DataFrame(prefs, columns=["Team", "Contact", "Size", "Preferred Days"])
            st.dataframe(df, use_container_width=True)
        else:
            st.write("No submitted preferences.")

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
            success = insert_preference(team_name, contact_person, team_size, preferred_days)
            if success:
                st.success("✅ Preference submitted successfully!")

# --- Oasis Individual Preference Form ---
st.header("Reserve Your Oasis Seat")
with st.form("oasis_preference_form"):
    person_name = st.text_input("Your Name:")
    selected_oasis_days = st.multiselect(
        "Select 2 preferred days for Oasis:",
        ["Monday", "Tuesday", "Wednesday", "Thursday"],
        max_selections=2
    )

    oasis_submitted = st.form_submit_button("Submit Oasis Preference")
    if oasis_submitted:
        if not person_name:
            st.warning("Please enter your name.")
        elif len(selected_oasis_days) != 2:
            st.warning("Please select exactly 2 days for Oasis.")
        else:
            preferred_days = ",".join(selected_oasis_days)
            success = insert_oasis_preference(person_name, preferred_days)
            if success:
                st.success("✅ Oasis preference submitted!")

# --- Room Allocation Grid ---
st.header("Current Room Allocations")
allocs = run_query("SELECT team_name, room_name, date FROM weekly_allocations", fetch=True)
if allocs:
    df = pd.DataFrame(allocs, columns=["Team", "Room", "Date"])
    df["Date"] = pd.to_datetime(df["Date"])
    df["Day"] = df["Date"].dt.strftime('%A')

    all_days = ["Monday", "Tuesday", "Wednesday", "Thursday"]
    all_rooms = sorted(set([room['name'] for room in AVAILABLE_ROOMS if room['name'] != 'Oasis']))
    pivot = df.pivot(index="Room", columns="Day", values="Team").fillna("Vacant")
    pivot = pivot.reindex(columns=all_days, fill_value="Vacant").reindex(index=all_rooms)

    st.dataframe(pivot, use_container_width=True)
else:
    st.write("No allocations available yet.")

st.caption("Manage voting and allocation directly from the admin panel above.")
