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

oasis = next((r for r in AVAILABLE_ROOMS if r["name"] == "Oasis"), {"capacity": 12})

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
            cur.execute("""
                SELECT wa.team_name, wp.contact_person, wa.room_name, wa.date
                FROM weekly_allocations wa
                LEFT JOIN weekly_preferences wp ON wa.team_name = wp.team_name
            """)
            data = cur.fetchall()
            if not data:
                return pd.DataFrame()
            df = pd.DataFrame(data, columns=["Team", "Contact", "Room", "Date"])
            df["Date"] = pd.to_datetime(df["Date"])
            df["Day"] = df["Date"].dt.strftime('%A')

            project_df = df[df["Room"] != "Oasis"]
            all_rooms = list({room["name"] for room in AVAILABLE_ROOMS if room["name"] != "Oasis"})
            all_days = ["Monday", "Tuesday", "Wednesday", "Thursday"]
            full_index = pd.MultiIndex.from_product([all_rooms, all_days], names=["Room", "Day"])

            project_df["Display"] = project_df["Team"] + " (" + project_df["Contact"] + ")"
            grouped = project_df.groupby(["Room", "Day"])["Display"].apply(lambda x: ", ".join(sorted(set(x))))
            grouped = grouped.reindex(full_index, fill_value="Vacant").reset_index()
            pivot = grouped.pivot(index="Room", columns="Day", values="Display").fillna("Vacant")
            pivot = pivot.reset_index()

            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday"]
            pivot = pivot[["Room"] + [day for day in day_order if day in pivot.columns]]

            return pivot
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
            grouped = grouped.rename(columns={"Day": "Weekday", "Person": "People"})

            return grouped
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
            cur.execute("SELECT person_name, preferred_day_1, preferred_day_2, submission_time FROM oasis_preferences")
            rows = cur.fetchall()
            return pd.DataFrame(rows, columns=["Person", "Day 1", "Day 2", "Submitted At"])
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

def insert_oasis(pool, person, day1, day2):
    conn = get_connection(pool)
    try:
        with conn.cursor() as cur:
            # Prevent duplicate
            cur.execute("SELECT 1 FROM oasis_preferences WHERE person_name = %s", (person,))
            if cur.fetchone():
                st.error("❌ You've already submitted. Contact admin to change your selection.")
                return False

            # Insert new vote
            cur.execute("""
                INSERT INTO oasis_preferences (person_name, preferred_day_1, preferred_day_2, submission_time)
                VALUES (%s, %s, %s, NOW())
            """, (person, day1, day2))
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
st.info("""
💡 **How This Works:**

- 🧑‍🤝‍🧑 Project teams can select **either Monday & Wednesday** or **Tuesday & Thursday**.
- 🌿 Oasis users can choose **any 2 weekdays**, and will be randomly assigned.
- ❗ You may only submit **once**. If you need to change your input, contact an admin.
- ✅ Allocations are refreshed **weekly** by an admin. You can vote until allocation is run (typically Friday 17:00).
""")


now_local = datetime.now(OFFICE_TIMEZONE)
st.info(f"Current Office Time: **{now_local.strftime('%Y-%m-%d %H:%M:%S')}** ({OFFICE_TIMEZONE_STR})")
pool = get_db_connection_pool()

# --- Admin ---
with st.expander("🔐 Admin Controls"):
    pwd = st.text_input("Enter admin password:", type="password")
    if pwd == RESET_PASSWORD:
        st.success("✅ Access granted.")

        if st.button("🚀 Run Allocation Now"):
            if run_allocation(DATABASE_URL):
                st.success("✅ Allocation completed.")
            else:
                st.error("❌ Allocation failed.")

        if st.button("🗑️ Reset Preferences"):
            if reset_preferences(pool):
                st.success("✅ Preferences cleared.")

        if st.button("🧼 Reset Allocations"):
            if reset_allocations(pool):
                st.success("✅ Allocations cleared.")

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
                                INSERT INTO oasis_preferences (person_name, preferred_day_1, preferred_day_2, submission_time)
                                VALUES (%s, %s, %s, NOW())
                            """, (row["Person"], row["Day 1"], row["Day 2"]))
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
    selected_days = st.multiselect(
        "Select Your 2 Preferred Days for Oasis:",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        max_selections=2
    )
    submit_oasis = st.form_submit_button("Submit Oasis Preference")

    if submit_oasis:
        if not person:
            st.error("❌ Please enter your name.")
        elif len(selected_days) != 2:
            st.error("❌ Select exactly 2 different days.")
        else:
            if insert_oasis(pool, person.strip(), selected_days[0], selected_days[1]):
                st.success("✅ Oasis preference submitted!")



# --- Allocations ---
st.header("📌 Project Room Allocations")
alloc_df = get_room_grid(pool)
if alloc_df.empty:
    st.write("No allocations yet.")
else:
    st.dataframe(alloc_df, use_container_width=True)

from datetime import timedelta

today = datetime.now(OFFICE_TIMEZONE).date()
this_monday = today - timedelta(days=today.weekday())

st.header("🆕 Add Yourself to Oasis Allocation")
with st.form("oasis_add_form"):
    new_name = st.text_input("Your Name")
    new_days = st.multiselect("Select one or more days:", ["Monday", "Tuesday", "Wednesday", "Thursday"])
    add_submit = st.form_submit_button("➕ Add me to the schedule")

    if add_submit:
        if not new_name.strip():
            st.error("❌ Please enter your name.")
        elif len(new_days) == 0:
            st.error("❌ Select at least one day.")
        else:
            conn = None
            try:
                conn = get_connection(pool)
                with conn.cursor() as cur:
                    name_clean = new_name.strip().title()

                    # Remove existing entries for this user
                    cur.execute("""
                        DELETE FROM weekly_allocations
                        WHERE room_name = 'Oasis' AND team_name = %s
                    """, (name_clean,))

                    for day in new_days:
                        date_obj = this_monday + timedelta(days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"].index(day))

                        # Check current occupancy
                        cur.execute("""
                            SELECT COUNT(*) FROM weekly_allocations
                            WHERE room_name = 'Oasis' AND date = %s
                        """, (date_obj,))
                        count = cur.fetchone()[0]

                        if count >= oasis["capacity"]:
                            st.warning(f"Oasis is full on {day}, not added.")
                        else:
                            cur.execute("""
                                INSERT INTO weekly_allocations (team_name, room_name, date)
                                VALUES (%s, 'Oasis', %s)
                            """, (name_clean, date_obj))

                    conn.commit()
                    st.success("✅ You're added to the selected days!")
            except Exception as e:
                st.error(f"❌ Error: {e}")
            finally:
                if conn:
                    return_connection(pool, conn)

from datetime import datetime, timedelta
import pandas as pd

st.header("📊 Full Weekly Oasis Overview")

today = datetime.now(OFFICE_TIMEZONE).date()
this_monday = today - timedelta(days=today.weekday())
days = [this_monday + timedelta(days=i) for i in range(5)]  # Monday to Friday
day_names = [d.strftime("%A") for d in days]
capacity = oasis["capacity"]

conn = get_connection(pool)
try:
    with conn.cursor() as cur:
        cur.execute("SELECT team_name, date FROM weekly_allocations WHERE room_name = 'Oasis'")
        rows = cur.fetchall()

    df = pd.DataFrame(rows, columns=["Name", "Date"])
    df["Date"] = pd.to_datetime(df["Date"]).dt.date

    unique_names = sorted(set(df["Name"]).union({"Niek"}))  # Always include Niek
    matrix = pd.DataFrame(False, index=unique_names, columns=day_names)

    for day, label in zip(days, day_names):
        signed_up = df[df["Date"] == day]["Name"]
        for name in signed_up:
            matrix.at[name, label] = True
    for day in day_names:
        matrix.at["Niek", day] = True  # Force Niek to always be signed up

    # --- Display availability ---
    st.subheader("🪑 Oasis Availability Summary")
    used_per_day = df.groupby("Date").size().to_dict()
    for day, label in zip(days, day_names):
        used = used_per_day.get(day, 0)
        if matrix.at["Niek", label]:
            used += 1 if "Niek" not in df[df["Date"] == day]["Name"].values else 0
        left = max(0, capacity - used)
        st.markdown(f"**{label}**: {left} spots left")

    # --- Display editable matrix ---
    edited = st.data_editor(
        matrix,
        use_container_width=True,
        disabled=["Niek"],
        key="oasis_matrix_editor"
    )

    if st.button("💾 Save Oasis Matrix"):
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM weekly_allocations WHERE room_name = 'Oasis' AND team_name != 'Niek'")
                inserted_counts = {day: 1 if matrix.at["Niek", day] else 0 for day in day_names}

                for name in edited.index:
                    if name == "Niek":
                        continue
                    for day in day_names:
                        if edited.at[name, day]:
                            if inserted_counts[day] < capacity:
                                date_obj = this_monday + timedelta(days=day_names.index(day))
                                cur.execute(
                                    "INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)",
                                    (name, "Oasis", date_obj)
                                )
                                inserted_counts[day] += 1
                            else:
                                st.warning(f"{name} could not be added to {day}: full.")
                conn.commit()
                st.success("✅ Matrix saved.")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to save matrix: {e}")

except Exception as e:
    st.error(f"❌ Error loading matrix: {e}")
finally:
    return_connection(pool, conn)
