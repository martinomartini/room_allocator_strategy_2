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
RESET_PASSWORD = "trainee"  # Admin password

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

def reset_allocations(pool):
    conn = get_connection_from_pool(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM weekly_allocations")
            cur.execute("DELETE FROM weekly_preferences")
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Failed to reset data: {e}")
        return False
    finally:
        return_connection_to_pool(pool, conn)

# --- Streamlit App UI ---

st.set_page_config(page_title="Weekly Room Allocator", layout="centered")
st.title("📅 Weekly Office Room Allocator")

now_local = datetime.now(OFFICE_TIMEZONE)
st.info(f"Current Office Time: **{now_local.strftime('%Y-%m-%d %H:%M:%S')}** ({OFFICE_TIMEZONE_STR})")

db_pool = get_db_connection_pool()

# --- Preference Form ---
st.header("Submit Your Preference for Next Week")
with st.form("weekly_preference_form"):
    team_name = st.text_input("Team Name:")
    contact_person = st.text_input("Contact Person:")
    team_size = st.number_input("Team Size:", min_value=1)
    selected_days = st.multiselect(
        "Select 2 preferred office days:",
        ["Monday", "Tuesday", "Wednesday", "Thursday"],
        max_selections=2
    )

    submitted = st.form_submit_button("Submit Preference")
    if submitted:
        if not team_name or not contact_person:
            st.warning("Please complete all fields.")
        elif len(selected_days) != 2:
            st.warning("Please select exactly two days.")
        else:
            preferred_days = ",".join(selected_days)
            if db_pool:
                success = insert_preference(db_pool, team_name, contact_person, team_size, preferred_days)
                if success:
                    st.success("✅ Preference submitted successfully!")

# --- Allocation Viewer ---
st.header("Room Allocations for This Week")
if db_pool:
    df = get_allocations(db_pool)
    if df.empty:
        st.write("🔄 No allocations found yet. Allocations will appear here once generated.")
    else:
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime('%A %Y-%m-%d')
        st.dataframe(df, use_container_width=True)

# --- Admin Reset ---
with st.expander("🔐 Admin: Reset Allocations Now"):
    password = st.text_input("Enter admin password:", type="password")
    if password == RESET_PASSWORD:
        if st.button("🚨 Reset Weekly Allocations and Preferences"):
            if db_pool and reset_allocations(db_pool):
                st.success("✅ All weekly data cleared.")
                st.rerun()
    elif password:
        st.error("❌ Incorrect password.")

st.divider()
st.caption("🔄 Preferences open every Friday. Allocations are made automatically each Saturday.")
