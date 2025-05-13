# app.py
import streamlit as st
import psycopg2
import psycopg2.pool
import json
import os
from datetime import datetime
import pytz
import pandas as pd
from allocate_rooms import run_allocation

# Configuration
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
with open(ROOMS_FILE, 'r') as f:
    AVAILABLE_ROOMS = json.load(f)

@st.cache_resource
def get_db_connection_pool():
    return psycopg2.pool.SimpleConnectionPool(1, 5, dsn=DATABASE_URL)

def get_connection(pool): return pool.getconn()
def return_connection(pool, conn): pool.putconn(conn)

# Database functions
def insert_preference(pool, team, contact, size, days):
    conn = get_connection(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT preferred_days FROM weekly_preferences WHERE team_name = %s", (team,))
            already = cur.fetchall()
            days_already = set()
            for r in already: days_already.update(r[0].split(','))
            new_days = set(days.split(','))
            if len(days_already) >= 2: st.error("Already voted for 2 days."); return False
            if len(days_already.union(new_days)) > 2: st.error("Voting would exceed 2 days."); return False
            cur.execute("INSERT INTO weekly_preferences (team_name, contact_person, team_size, preferred_days, submission_time) VALUES (%s,%s,%s,%s,NOW())", (team, contact, size, days))
            conn.commit()
            return True
    except Exception as e:
        st.error(f"❌ {e}")
        return False
    finally:
        return_connection(pool, conn)

def insert_oasis(pool, person, days):
    conn = get_connection(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO oasis_preferences (person_name, preferred_days, submission_time) VALUES (%s, %s, NOW())", (person, days))
            conn.commit()
            return True
    except Exception as e:
        st.error(f"❌ {e}")
        return False
    finally:
        return_connection(pool, conn)

def reset_allocations(pool):
    conn = get_connection(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM weekly_allocations")
            conn.commit()
            return True
    finally:
        return_connection(pool, conn)

def reset_preferences(pool):
    conn = get_connection(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM weekly_preferences")
            cur.execute("DELETE FROM oasis_preferences")
            conn.commit()
            return True
    finally:
        return_connection(pool, conn)

def get_preferences(pool):
    conn = get_connection(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT team_name, contact_person, team_size, preferred_days FROM weekly_preferences")
            return pd.DataFrame(cur.fetchall(), columns=["Team", "Contact", "Size", "Days"])
    finally:
        return_connection(pool, conn)

def get_oasis_preferences(pool):
    conn = get_connection(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT person_name, preferred_days, submission_time FROM oasis_preferences")
            return pd.DataFrame(cur.fetchall(), columns=["Person", "Preferred Days", "Submitted At"])
    finally:
        return_connection(pool, conn)

def get_allocation_grid(pool):
    conn = get_connection(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT team_name, room_name, date FROM weekly_allocations")
            df = pd.DataFrame(cur.fetchall(), columns=["Team", "Room", "Date"])
            df["Date"] = pd.to_datetime(df["Date"])
            df["Day"] = df["Date"].dt.strftime('%A')
            pivot = df.pivot(index="Room", columns="Day", values="Team").fillna("Vacant")
            return pivot.reset_index()
    finally:
        return_connection(pool, conn)

# UI
st.title("📅 Weekly Room Allocator")
now_local = datetime.now(OFFICE_TIMEZONE)
st.info(f"Current Office Time: **{now_local.strftime('%Y-%m-%d %H:%M:%S')}** ({OFFICE_TIMEZONE_STR})")
pool = get_db_connection_pool()

# Admin Panel
with st.expander("🔐 Admin Controls"):
    pwd = st.text_input("Enter admin password:", type="password")
    if pwd == RESET_PASSWORD:
        if st.button("🚀 Run Allocation Now"):
            if run_allocation(): st.success("Allocations updated.")
            else: st.error("Something went wrong.")
        if st.button("🗑️ Reset Preferences"): reset_preferences(pool); st.success("Preferences reset.")
        if st.button("🧼 Reset Allocations"): reset_allocations(pool); st.success("Allocations reset.")

        df1 = get_preferences(pool)
        df2 = get_oasis_preferences(pool)
        if not df1.empty:
            st.subheader("Team Preferences")
            st.dataframe(df1)
        if not df2.empty:
            st.subheader("Oasis Preferences")
            st.dataframe(df2)

# Submit Form (Team)
st.header("Submit Your Preference for Next Week")
with st.form("team_form"):
    name = st.text_input("Team Name")
    contact = st.text_input("Contact Person")
    size = st.number_input("Team Size", min_value=1, max_value=5)
    days = st.selectbox("Choose preferred days", ["Monday and Wednesday", "Tuesday and Thursday"])
    if st.form_submit_button("Submit Preference"):
        final = "Monday,Wednesday" if "Monday" in days else "Tuesday,Thursday"
        if insert_preference(pool, name, contact, size, final):
            st.success("Submitted!")

# Submit Form (Oasis)
st.header("Reserve Your Oasis Seat")
with st.form("oasis_form"):
    person = st.text_input("Your Name")
    days = st.selectbox("Choose preferred days for Oasis", ["Monday and Wednesday", "Tuesday and Thursday"])
    if st.form_submit_button("Submit Oasis Preference"):
        final = "Monday,Wednesday" if "Monday" in days else "Tuesday,Thursday"
        if insert_oasis(pool, person, final):
            st.success("Submitted!")

# Allocation Table
st.header("Current Room Allocations")
df = get_allocation_grid(pool)
if df.empty:
    st.write("No allocations available yet.")
else:
    st.dataframe(df, use_container_width=True)

st.caption("Tabular view of weekly room allocations and submissions.")
