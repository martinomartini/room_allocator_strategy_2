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
st.set_page_config(page_title="Weekly Room Allocator", layout="wide")
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

# --- DB Functions ---
def get_room_grid(pool):
    conn = get_connection(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT team_name, room_name, date FROM weekly_allocations")
            data = cur.fetchall()
            if not data:
                return pd.DataFrame()
            df = pd.DataFrame(data, columns=["Team", "Room", "Date"])
            df["Date"] = pd.to_datetime(df["Date"])
            df["Day"] = df["Date"].dt.strftime('%A')

            project_df = df[df["Room"] != "Oasis"]
            all_rooms = list({room["name"] for room in AVAILABLE_ROOMS if room["name"] != "Oasis"})
            all_days = ["Monday", "Tuesday", "Wednesday", "Thursday"]
            full_index = pd.MultiIndex.from_product([all_rooms, all_days], names=["Room", "Day"])

            grouped = project_df.groupby(["Room", "Day"])["Team"].apply(lambda x: ", ".join(sorted(set(x))))
            grouped = grouped.reindex(full_index, fill_value="Vacant").reset_index()
            pivot = grouped.pivot(index="Room", columns="Day", values="Team").fillna("Vacant")
            return pivot.reset_index()
    except Exception as e:
        st.warning(f"Failed to load allocation data: {e}")
        return pd.DataFrame()
    finally:
        return_connection(pool, conn)

def get_oasis_grid(pool):
    conn = get_connection(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT team_name, room_name, date FROM weekly_allocations WHERE room_name = 'Oasis'")
            data = cur.fetchall()
            if not data:
                return pd.DataFrame()
            df = pd.DataFrame(data, columns=["Person", "Room", "Date"])
            df["Date"] = pd.to_datetime(df["Date"])
            df["Day"] = df["Date"].dt.strftime('%A')

            all_days = ["Monday", "Tuesday", "Wednesday", "Thursday"]
            grouped = df.groupby("Day")["Person"].apply(lambda x: ", ".join(sorted(set(x))))
            grouped = grouped.reindex(all_days, fill_value="Vacant").reset_index()
            return grouped.rename(columns={"Day": "Weekday", "Person": "People"})
    except Exception as e:
        st.warning(f"Failed to load oasis allocation data: {e}")
        return pd.DataFrame()
    finally:
        return_connection(pool, conn)

def get_preferences(pool):
    conn = get_connection(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT team_name, contact_person, team_size, preferred_days FROM weekly_preferences")
            rows = cur.fetchall()
            return pd.DataFrame(rows, columns=["Team", "Contact", "Size", "Days"])
    except Exception as e:
        st.warning(f"Failed to fetch preferences: {e}")
        return pd.DataFrame()
    finally:
        return_connection(pool, conn)

def get_oasis_preferences(pool):
    conn = get_connection(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT person_name, preferred_days, submission_time FROM oasis_preferences")
            rows = cur.fetchall()
            return pd.DataFrame(rows, columns=["Person", "Preferred Days", "Submitted At"])
    except Exception as e:
        st.warning(f"Failed to fetch oasis preferences: {e}")
        return pd.DataFrame()
    finally:
        return_connection(pool, conn)

def insert_preference(pool, team, contact, size, days):
    if size > 5:
        st.error("❌ Team size cannot exceed 5.")
        return False
    conn = get_connection(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT preferred_days FROM weekly_preferences WHERE team_name = %s", (team,))
            existing = cur.fetchall()
            voted_days = set(d for row in existing for d in row[0].split(','))
            new_days = set(days.split(','))
            if len(voted_days) >= 2 or len(voted_days.union(new_days)) > 2:
                st.error("❌ Max 2 days allowed per team.")
                return False
            if not (new_days == {"Monday", "Wednesday"} or new_days == {"Tuesday", "Thursday"}):
                st.error("❌ Must select Monday & Wednesday or Tuesday & Thursday.")
                return False
            cur.execute("""
                INSERT INTO weekly_preferences (team_name, contact_person, team_size, preferred_days, submission_time)
                VALUES (%s, %s, %s, %s, NOW())
            """, (team, contact, size, days))
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Insert failed: {e}")
        return False
    finally:
        return_connection(pool, conn)

def insert_oasis(pool, person, days):
    conn = get_connection(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO oasis_preferences (person_name, preferred_days, submission_time)
                VALUES (%s, %s, NOW())
            """, (person, days))
            conn.commit()
            return True
    except Exception as e:
        st.error(f"Oasis insert failed: {e}")
        return False
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

def reset_allocations(pool):
    conn = get_connection(pool)
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM weekly_allocations")
            conn.commit()
            return True
    finally:
        return_connection(pool, conn)

# --- UI ---
st.title("📅 Weekly Room Allocator")
now_local = datetime.now(OFFICE_TIMEZONE)
st.info(f"Current Office Time: **{now_local.strftime('%Y-%m-%d %H:%M:%S')}** ({OFFICE_TIMEZONE_STR})")
pool = get_db_connection_pool()

# --- Admin ---
with st.expander("🔐 Admin Controls"):
    pwd = st.text_input("Enter admin password:", type="password")
    if pwd == RESET_PASSWORD:
        st.success("✅ Access granted.")

        # Run allocation and capture unplaced teams
        if st.button("🚀 Run Allocation Now"):
            success, unplaced = run_allocation(DATABASE_URL)
            if success:
                st.success("✅ Allocation completed.")
                if unplaced:
                    st.warning("⚠️ The following teams could not be placed on any day:")
                    st.write(", ".join(unplaced))
                else:
                    st.info("🎉 All teams were successfully placed at least once.")
            else:
                st.error("❌ Allocation failed.")

        if st.button("🗑️ Reset Preferences"):
            if reset_preferences(pool):
                st.success("✅ Preferences cleared.")

        if st.button("🧼 Reset Allocations"):
            if reset_allocations(pool):
                st.success("✅ Allocations cleared.")
    elif pwd:
        st.error("❌ Incorrect password.")


        # --- Editable Team Preferences ---
        st.subheader("🧾 Team Preferences")
        df1 = get_preferences(pool)
        if not df1.empty:
            editable_team_df = st.data_editor(df1, num_rows="dynamic", use_container_width=True, key="edit_teams")
            if st.button("💾 Save Team Changes"):
                try:
                    conn = get_connection(pool)
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM weekly_preferences")
                        for _, row in editable_team_df.iterrows():
                            cur.execute("""
                                INSERT INTO weekly_preferences (team_name, contact_person, team_size, preferred_days, submission_time)
                                VALUES (%s, %s, %s, %s, NOW())
                            """, (row["Team"], row["Contact"], int(row["Size"]), row["Days"]))
                        conn.commit()
                    st.success("✅ Team preferences updated.")
                except Exception as e:
                    st.error(f"❌ Failed to update team preferences: {e}")
                finally:
                    return_connection(pool, conn)
        else:
            st.info("No team preferences submitted yet.")

        # --- Editable Oasis Preferences ---
        st.subheader("🌿 Oasis Preferences")
        df2 = get_oasis_preferences(pool)
        if not df2.empty:
            editable_oasis_df = st.data_editor(df2, num_rows="dynamic", use_container_width=True, key="edit_oasis")
            if st.button("💾 Save Oasis Changes"):
                try:
                    conn = get_connection(pool)
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM oasis_preferences")
                        for _, row in editable_oasis_df.iterrows():
                            cur.execute("""
                                INSERT INTO oasis_preferences (person_name, preferred_days, submission_time)
                                VALUES (%s, %s, NOW())
                            """, (row["Person"], row["Preferred Days"]))
                        conn.commit()
                    st.success("✅ Oasis preferences updated.")
                except Exception as e:
                    st.error(f"❌ Failed to update oasis preferences: {e}")
                finally:
                    return_connection(pool, conn)
        else:
            st.info("No oasis preferences submitted yet.")

    elif pwd:
        st.error("❌ Incorrect password.")


# --- Team Form ---
st.header("Submit Team Preference")
with st.form("team_form"):
    name = st.text_input("Team Name")
    contact = st.text_input("Contact Person")
    size = st.number_input("Team Size", min_value=1, max_value=5)
    choice = st.selectbox("Preferred Days", ["Monday and Wednesday", "Tuesday and Thursday"])
    submit = st.form_submit_button("Submit")
    if submit:
        day_map = {
            "Monday and Wednesday": "Monday,Wednesday",
            "Tuesday and Thursday": "Tuesday,Thursday"
        }
        if insert_preference(pool, name, contact, size, day_map[choice]):
            st.success("✅ Submitted!")

# --- Oasis Form ---
st.header("Reserve Oasis Seat")
with st.form("oasis_form"):
    person = st.text_input("Your Name")
    oasis_day = st.selectbox("Preferred Days", ["Monday and Wednesday", "Tuesday and Thursday"])
    submit_oasis = st.form_submit_button("Submit Oasis Preference")
    if submit_oasis:
        day_map = {
            "Monday and Wednesday": "Monday,Wednesday",
            "Tuesday and Thursday": "Tuesday,Thursday"
        }
        if insert_oasis(pool, person, day_map[oasis_day]):
            st.success("✅ Oasis vote submitted!")

# --- Allocations Table ---
st.header("📌 Project Room Allocations")
alloc_df = get_room_grid(pool)
if alloc_df.empty:
    st.write("No allocations yet.")
else:
    st.dataframe(alloc_df, use_container_width=True)

st.header("🌿 Oasis Seat Allocations")
oasis_df = get_oasis_grid(pool)
if oasis_df.empty:
    st.write("No oasis allocations yet.")
else:
    st.dataframe(oasis_df, use_container_width=True)

st.caption("Room grid is based on weekly_allocations table. Made by Martino Martini")
