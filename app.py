import streamlit as st
import psycopg2
import psycopg2.pool
import json
import os
from datetime import datetime, timedelta
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

oasis = next((r for r in AVAILABLE_ROOMS if r["name"] == "Oasis"), {"capacity": 12})

@st.cache_resource
def get_db_connection_pool():
    return psycopg2.pool.SimpleConnectionPool(1, 5, dsn=DATABASE_URL)

def get_connection(pool): return pool.getconn()
def return_connection(pool, conn): pool.putconn(conn)

# --- UI ---
st.title("📅 Weekly Room Allocator")
st.info("""
💡 **How This Works:**

- 🧑‍🤝‍🧑 Project teams can select **Monday & Wednesday** or **Tuesday & Thursday**.
- 🌿 Oasis users can pick **any 2 days**. The admin assigns days via random allocation.
- ✅ After allocation, users can **freely edit** their days anytime.
- 🔒 Submitting a preference locks it (editable only by admin before allocation).
- 🕒 Allocation runs every week and resets for the new week.
""")

pool = get_db_connection_pool()

# --- Admin ---
with st.expander("🔐 Admin Controls"):
    pwd = st.text_input("Enter admin password:", type="password")
    if pwd == RESET_PASSWORD:
        st.success("✅ Access granted.")

        if st.button("🚀 Run Allocation Now"):
            success, unplaced = run_allocation(DATABASE_URL)
            if success:
                st.success("✅ Allocation completed.")
                if unplaced:
                    st.warning(f"Not placed: {', '.join(unplaced)}")
            else:
                st.error("❌ Allocation failed.")

        if st.button("🗑️ Reset Preferences"):
            conn = get_connection(pool)
            with conn.cursor() as cur:
                cur.execute("DELETE FROM weekly_preferences")
                cur.execute("DELETE FROM oasis_preferences")
                conn.commit()
            return_connection(pool, conn)
            st.success("✅ Preferences cleared.")

        if st.button("🧼 Reset Allocations"):
            conn = get_connection(pool)
            with conn.cursor() as cur:
                cur.execute("DELETE FROM weekly_allocations")
                conn.commit()
            return_connection(pool, conn)
            st.success("✅ Allocations cleared.")

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
        conn = get_connection(pool)
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM weekly_preferences WHERE team_name = %s", (name,))
                if cur.fetchone():
                    st.error("❌ Already submitted.")
                else:
                    cur.execute("""
                        INSERT INTO weekly_preferences (team_name, contact_person, team_size, preferred_days, submission_time)
                        VALUES (%s, %s, %s, %s, NOW())
                    """, (name, contact, size, day_map[choice]))
                    conn.commit()
                    st.success("✅ Submitted!")
        except Exception as e:
            st.error(f"Insert failed: {e}")
        finally:
            return_connection(pool, conn)

# --- Oasis Preference Phase ---
st.header("🌿 Submit Oasis Preferences")
with st.form("oasis_form"):
    person = st.text_input("Your Name")
    selected_days = st.multiselect(
        "Select 2 Preferred Days",
        ["Monday", "Tuesday", "Wednesday", "Thursday"],
        max_selections=2
    )
    submit_oasis = st.form_submit_button("Submit Oasis Preference")
    if submit_oasis:
        if len(selected_days) != 2:
            st.error("❌ Select exactly 2 days.")
        else:
            conn = get_connection(pool)
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM oasis_preferences WHERE person_name = %s", (person,))
                    if cur.fetchone():
                        st.error("❌ Already submitted. Ask admin to reset.")
                    else:
                        cur.execute("""
                            INSERT INTO oasis_preferences (person_name, preferred_day_1, preferred_day_2, submission_time)
                            VALUES (%s, %s, %s, NOW())
                        """, (person, selected_days[0], selected_days[1]))
                        conn.commit()
                        st.success("✅ Preference submitted!")
            except Exception as e:
                st.error(f"Oasis insert failed: {e}")
            finally:
                return_connection(pool, conn)

# --- Oasis Weekly Grid (Editable by Users) ---
st.header("🧾 Update Your Weekly Oasis Days")

today = datetime.now(OFFICE_TIMEZONE).date()
this_monday = today - timedelta(days=today.weekday())
days = [(this_monday + timedelta(days=i)) for i in range(4)]
day_labels = [d.strftime("%a %d %b") for d in days]

conn = get_connection(pool)
with conn.cursor() as cur:
    # Load current usage
    cur.execute("SELECT date, COUNT(*) FROM weekly_allocations WHERE room_name = 'Oasis' GROUP BY date")
    counts = dict(cur.fetchall())

    person_name = st.text_input("🙋 Your Name to Edit Days")
    if person_name:
        cur.execute("SELECT date FROM weekly_allocations WHERE team_name = %s AND room_name = 'Oasis'", (person_name,))
        existing_days = [r[0] for r in cur.fetchall()]

        selected_days = []
        cols = st.columns(4)
        for i, (col, label, day) in enumerate(zip(cols, day_labels, days)):
            spots_left = oasis["capacity"] - counts.get(day, 0)
            already_selected = day in existing_days
            with col:
                st.markdown(f"**{label}**")
                st.markdown(f"🪑 {spots_left} spot{'s' if spots_left != 1 else ''} left")
                checked = st.checkbox("", key=f"{person_name}_{day}", value=already_selected)
                if checked:
                    selected_days.append(day)

        if st.button("💾 Save My Oasis Days"):
            cur.execute("DELETE FROM weekly_allocations WHERE team_name = %s AND room_name = 'Oasis'", (person_name,))
            for day in selected_days:
                cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)",
                            (person_name, "Oasis", day))
            conn.commit()
            st.success("✅ Updated your selections!")

return_connection(pool, conn)

# --- Overview
st.header("📌 Oasis Allocation Overview")
conn = get_connection(pool)
with conn.cursor() as cur:
    cur.execute("SELECT team_name, date FROM weekly_allocations WHERE room_name = 'Oasis'")
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=["Name", "Date"])
    df["Date"] = pd.to_datetime(df["Date"])
    df["Day"] = df["Date"].dt.strftime("%a %d %b")
    pivot = df.pivot_table(index="Name", columns="Day", aggfunc=len, fill_value="")
    st.dataframe(pivot)
return_connection(pool, conn)

st.caption("Made by Martino Martini ✨")
