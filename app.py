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
            if run_allocation():
                st.success("✅ Allocation completed.")
            else:
                st.error("❌ Allocation failed. See logs.")

        if st.button("🗑️ Reset Preferences"):
            if reset_preferences(db_pool):
                st.success("✅ Preferences reset.")

        if st.button("🧼 Reset Allocations"):
            if reset_allocations(db_pool):
                st.success("✅ Allocations reset.")
    elif password:
        st.error("❌ Incorrect password.")

# --- Allocation View ---
st.header("Current Room Allocations")
if db_pool:
    grid = get_room_grid(db_pool)
    if grid.empty:
        st.write("No allocations available yet.")
    else:
        st.dataframe(grid, use_container_width=True)

st.divider()
st.caption("Tabular view generated from the weekly_allocations table")
