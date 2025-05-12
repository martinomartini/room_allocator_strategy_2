# app.py
import streamlit as st
import psycopg2
import psycopg2.pool
import json
import os
from datetime import datetime, timedelta
import pytz
import pandas as pd

# --- Configuration ---

DATABASE_URL = st.secrets.get("SUPABASE_DB_URI", os.environ.get("SUPABASE_DB_URI"))
OFFICE_TIMEZONE_STR = st.secrets.get("OFFICE_TIMEZONE", os.environ.get("OFFICE_TIMEZONE", "UTC"))

try:
    OFFICE_TIMEZONE = pytz.timezone(OFFICE_TIMEZONE_STR)
except pytz.exceptions.UnknownTimeZoneError:
    st.error(f"Invalid Timezone configured: '{OFFICE_TIMEZONE_STR}'. Defaulting to UTC.")
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
                INSERT INTO weekly_preferences (team_name, contact_person, team_size, preferred_days, submission_time)
                VALUES (%s, %s, %s, %s, NOW())
            """, (team_name, contact_person, team_size, preferred_days))
            conn.commit()
    except Exception as e:
        st.error(f"Failed to save preference: {e}")
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

# --- Streamlit App UI ---

st.set_page_config(page_title="Weekly Room Allocator", layout="centered")
st.title("📅 Weekly Office Room Allocator")

now_local = datetime.now(OFFICE_TIMEZONE)
day_name = now_local.strftime('%A')

st.info(f"Current Office Time: **{now_local.strftime('%Y-%m-%d %H:%M:%S')}** ({OFFICE_TIMEZONE_STR})")

# --- Preference Form (Fridays only) ---
if day_name == 'Friday':
    st.header("Submit Your Preference for Next Week")
    with st.form("weekly_preference_form"):
        team_name = st.text_input("Team Name:")
        contact_person = st.text_input("Contact Person:")
        team_size = st.number_input("Team Size:", min_value=1)
        preferred_days = st.radio("Preferred Office Days:", ["Mon + Wed", "Tue + Thu"])

        submitted = st.form_submit_button("Submit Preference")
        if submitted:
            if not team_name or not contact_person:
                st.warning("Please complete all fields.")
            else:
                db_pool = get_db_connection_pool()
                if db_pool:
                    insert_preference(db_pool, team_name, contact_person, team_size, preferred_days)
                    st.success("✅ Preference submitted successfully!")

# --- Weekly Allocation Display (Sat onward) ---
elif day_name in ['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']:
    st.header("Room Allocations for This Week")
    db_pool = get_db_connection_pool()
    if db_pool:
        df = get_allocations(db_pool)
        if df.empty:
            st.write("🔄 Allocations will appear here once available (every Saturday).")
        else:
            df["Date"] = pd.to_datetime(df["Date"]).dt.strftime('%A %Y-%m-%d')
            st.dataframe(df, use_container_width=True)

st.divider()
st.caption("🔄 Preferences open every Friday. Allocations are made automatically each Saturday.")
