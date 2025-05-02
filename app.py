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

def get_current_reservations_df(pool):
    reservations = []
    conn = get_connection_from_pool(pool)
    if not conn:
        return pd.DataFrame()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT team_name, contact_person, team_size, assigned_room_name,
                       to_char(reservation_time AT TIME ZONE %s, 'YYYY-MM-DD HH24:MI') as reservation_time_local
                FROM reservations
                ORDER BY assigned_room_name ASC
            """, (OFFICE_TIMEZONE_STR,))
            results = cur.fetchall()
            colnames = [desc[0] for desc in cur.description]
            reservations = [dict(zip(colnames, row)) for row in results]
    except:
        pass
    finally:
        return_connection_to_pool(pool, conn)

    if reservations:
        df = pd.DataFrame(reservations)
        df.columns = ["Team Name", "Contact", "Size", "Assigned Room", "Reserved At (Local)"]
        return df
    else:
        return pd.DataFrame()

# --- Streamlit App UI ---

st.set_page_config(page_title="Office Room Allocator", layout="centered")
st.title("🏢 Office Room Allocator")

now_local = datetime.now(OFFICE_TIMEZONE)
st.info(f"""
Current Office Time ({OFFICE_TIMEZONE_STR}): **{now_local.strftime('%Y-%m-%d %H:%M:%S')}**

Reservations are **🟢 always open**, and reset daily at 18:00 (office time).
""")

st.header("Make a Reservation")

form_disabled = False  # Always enabled

with st.form("reservation_form", clear_on_submit=True):
    team_name = st.text_input("Your Team Name:", placeholder="e.g., Project Phoenix", disabled=form_disabled)
    contact_person = st.text_input("Contact Person:", placeholder="e.g., Jane Doe", disabled=form_disabled)
    team_size = st.number_input("Team Size (Number of People):", min_value=1, step=1, disabled=form_disabled)

    submitted = st.form_submit_button("Find and Reserve Room", disabled=form_disabled)

    if submitted:
        if not team_name or not contact_person or team_size <= 0:
            st.warning("⚠️ Please fill in all fields correctly.")
        else:
            with st.spinner("Checking availability..."):
                db_pool = get_db_connection_pool()
                if not db_pool:
                    st.error("Database connection failed.")
                else:
                    conn = get_connection_from_pool(db_pool)
                    if not conn:
                        st.error("Could not get database connection.")
                    else:
                        try:
                            with conn.cursor() as cur:
                                cur.execute("SELECT DISTINCT assigned_room_name FROM reservations")
                                taken = set(row[0] for row in cur.fetchall())

                            suitable_rooms = sorted(
                                [r for r in AVAILABLE_ROOMS if r['capacity'] >= team_size and r['name'] not in taken],
                                key=lambda x: x['capacity']
                            )

                            if not suitable_rooms:
                                st.error(f"No available room found for a team of {team_size}.")
                            else:
                                assigned = suitable_rooms[0]['name']
                                with conn.cursor() as cur:
                                    cur.execute(
                                        "INSERT INTO reservations (team_name, contact_person, team_size, assigned_room_name) VALUES (%s, %s, %s, %s)",
                                        (team_name, contact_person, team_size, assigned)
                                    )
                                conn.commit()
                                st.success(f"✅ Reserved room '{assigned}' for team '{team_name}'!")
                        except Exception as e:
                            st.error(f"Reservation failed: {e}")
                            try:
                                conn.rollback()
                            except:
                                pass
                        finally:
                            return_connection_to_pool(db_pool, conn)

# --- Current Reservations ---

st.divider()
st.header("Current Reservations for Today")
st.caption(f"Showing reservations for {now_local.strftime('%Y-%m-%d')}.")

with st.spinner("Loading current reservations..."):
    db_pool = get_db_connection_pool()
    reservations_df = get_current_reservations_df(db_pool)

if reservations_df.empty:
    st.write("No rooms reserved yet for today.")
else:
    st.dataframe(reservations_df, hide_index=True, use_container_width=True)

st.divider()
st.caption("System resets daily at 18:00. You can reserve rooms anytime, subject to availability.")
