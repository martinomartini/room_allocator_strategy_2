import streamlit as st
import psycopg2
import psycopg2.pool
import json
import os
from datetime import datetime, timedelta, date # Ensure 'date' is imported
import pytz
import pandas as pd
from psycopg2.extras import RealDictCursor
from allocate_rooms import run_allocation  # Assuming this file exists and is correct

# -----------------------------------------------------
# Configuration and Global Constants
# -----------------------------------------------------
st.set_page_config(page_title="Weekly Room Allocator - TS", layout="wide")

DATABASE_URL = st.secrets.get("SUPABASE_DB_URI", os.environ.get("SUPABASE_DB_URI"))
OFFICE_TIMEZONE_STR = st.secrets.get("OFFICE_TIMEZONE", os.environ.get("OFFICE_TIMEZONE", "UTC"))
RESET_PASSWORD = "trainee"  # Consider moving to secrets

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
except FileNotFoundError:
    st.error(f"Error: {ROOMS_FILE} not found. Please ensure it exists in the application directory.")
    AVAILABLE_ROOMS = []
oasis = next((r for r in AVAILABLE_ROOMS if r["name"] == "Oasis"), {"capacity": 15})

# -----------------------------------------------------
# Database Connection Pool
# -----------------------------------------------------
@st.cache_resource
def get_db_connection_pool():
    if not DATABASE_URL:
        st.error("Database URL is not configured. Please set SUPABASE_DB_URI.")
        return None
    return psycopg2.pool.SimpleConnectionPool(1, 25, dsn=DATABASE_URL)

def get_connection(pool):
    if pool: return pool.getconn()
    return None

def return_connection(pool, conn):
    if pool and conn: pool.putconn(conn)

pool = get_db_connection_pool()

# -----------------------------------------------------
# Helper to load/update display dates and UI texts
# -----------------------------------------------------

# MODIFICATION: Set the default *date object* for data fetching for new sessions.
# This was the change from the previous response.
current_week_monday_init = date(2025, 6, 2) # Default to Monday, June 2nd, 2025

if "project_rooms_display_monday" not in st.session_state:
    st.session_state.project_rooms_display_monday = current_week_monday_init
if "oasis_display_monday" not in st.session_state:
    st.session_state.oasis_display_monday = current_week_monday_init

# MODIFICATION: Set more stable *default header texts* for new sessions,
# especially when the default June 2nd week is active.
# These can still be overridden by admin edits or by running allocations for other weeks.

# For submission form's "week of" text
default_submission_week_of_text_target = "2 June" # Corresponds to date(2025, 6, 2)
if "submission_week_of_text" not in st.session_state:
    # If the display Monday is our target June 2nd, use the fixed text. Otherwise, format it.
    if st.session_state.project_rooms_display_monday == date(2025, 6, 2):
        st.session_state["submission_week_of_text"] = default_submission_week_of_text_target
    else:
        st.session_state["submission_week_of_text"] = st.session_state.project_rooms_display_monday.strftime("%-d %B")

# For the main "Project Room Allocations" display header
default_project_alloc_markdown_target = "Displaying project rooms for the week of 2 June 2025."
if "project_allocations_display_markdown_content" not in st.session_state:
    if st.session_state.project_rooms_display_monday == date(2025, 6, 2):
        st.session_state["project_allocations_display_markdown_content"] = default_project_alloc_markdown_target
    else:
        st.session_state["project_allocations_display_markdown_content"] = f"Displaying project rooms for the week of {st.session_state.project_rooms_display_monday.strftime('%-d %B %Y')}."

# For the main "Oasis Allocations" display header
default_oasis_alloc_markdown_target = "Displaying Oasis for the week of 2 June 2025."
if "oasis_allocations_display_markdown_content" not in st.session_state:
    if st.session_state.oasis_display_monday == date(2025, 6, 2):
        st.session_state["oasis_allocations_display_markdown_content"] = default_oasis_alloc_markdown_target
    else:
        st.session_state["oasis_allocations_display_markdown_content"] = f"Displaying Oasis for the week of {st.session_state.oasis_display_monday.strftime('%-d %B %Y')}."

# These texts seem to be intended as fixed for the June 2nd week context.
if "submission_start_text" not in st.session_state:
    st.session_state["submission_start_text"] = "Wednesday 4 June 09:00" # Corresponds to week of June 2nd
if "submission_end_text" not in st.session_state:
    st.session_state["submission_end_text"] = "Thursday 5 June 16:00" # Corresponds to week of June 2nd
if "oasis_end_text" not in st.session_state:
    st.session_state["oasis_end_text"] = "Friday 6 June 16:00" # Corresponds to week of June 2nd


# -----------------------------------------------------
# Database Utility Functions
# -----------------------------------------------------
def get_room_grid(pool, display_monday: date):
    if not pool: return pd.DataFrame()
    this_monday = display_monday
    day_mapping = {
        this_monday + timedelta(days=0): "Monday", this_monday + timedelta(days=1): "Tuesday",
        this_monday + timedelta(days=2): "Wednesday", this_monday + timedelta(days=3): "Thursday"
    }
    day_labels = list(day_mapping.values())
    try:
        with open(ROOMS_FILE) as f: all_rooms = [r["name"] for r in json.load(f) if r["name"] != "Oasis"]
    except (FileNotFoundError, json.JSONDecodeError):
        st.error(f"Error: Could not load valid data from {ROOMS_FILE}.")
        return pd.DataFrame()
    grid = {room: {**{"Room": room}, **{day: "Vacant" for day in day_labels}} for room in all_rooms}
    conn = get_connection(pool)
    if not conn: return pd.DataFrame(grid.values())
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            start_date, end_date = this_monday, this_monday + timedelta(days=3) 
            cur.execute("""
                SELECT team_name, room_name, date FROM weekly_allocations
                WHERE room_name != 'Oasis' AND date >= %s AND date <= %s
            """, (start_date, end_date))
            allocations = cur.fetchall()
            cur.execute("SELECT team_name, contact_person FROM weekly_preferences") 
            contacts = {row["team_name"]: row["contact_person"] for row in cur.fetchall()}
        for row in allocations:
            team, room, date_val = row["team_name"], row["room_name"], row["date"]
            day = day_mapping.get(date_val)
            if room not in grid or not day: continue
            contact = contacts.get(team)
            grid[room][day] = f"{team} ({contact})" if contact else team
        return pd.DataFrame(grid.values())
    except psycopg2.Error as e:
        st.warning(f"Database error while getting room grid: {e}")
        return pd.DataFrame(grid.values())
    finally: return_connection(pool, conn)

def get_preferences(pool):
    if not pool: return pd.DataFrame()
    conn = get_connection(pool)
    if not conn: return pd.DataFrame()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT team_name, contact_person, team_size, preferred_days, submission_time FROM weekly_preferences ORDER BY submission_time DESC")
            rows = cur.fetchall()
            return pd.DataFrame(rows, columns=["Team", "Contact", "Size", "Days", "Submitted At"])
    except Exception as e:
        st.warning(f"Failed to fetch preferences: {e}")
        return pd.DataFrame()
    finally: return_connection(pool, conn)

def get_oasis_preferences(pool):
    if not pool: return pd.DataFrame()
    conn = get_connection(pool)
    if not conn: return pd.DataFrame()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT person_name, preferred_day_1, preferred_day_2, preferred_day_3, preferred_day_4, preferred_day_5, submission_time FROM oasis_preferences ORDER BY submission_time DESC")
            rows = cur.fetchall()
            return pd.DataFrame(rows, columns=["Person", "Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Submitted At"])
    except Exception as e:
        st.warning(f"Failed to fetch oasis preferences: {e}")
        return pd.DataFrame()
    finally: return_connection(pool, conn)

# -----------------------------------------------------
# Insert / Update Functions
# -----------------------------------------------------
def insert_preference(pool, team, contact, size, days):
    if not pool: return False
    if not team or not contact:
        st.error("❌ Team Name and Contact Person are required.")
        return False
    if not 3 <= size <= 6: 
        st.error("❌ Team size must be between 3 and 6.")
        return False
    conn = get_connection(pool)
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM weekly_preferences WHERE team_name = %s", (team,))
            if cur.fetchone():
                st.error(f"❌ Team '{team}' has already submitted a preference. Contact admin to change.")
                return False
            new_days_set = set(days.split(','))
            valid_pairs = [set(["Monday", "Wednesday"]), set(["Tuesday", "Thursday"])]
            if new_days_set not in valid_pairs:
                st.error("❌ Invalid day selection. Must select Monday & Wednesday or Tuesday & Thursday.")
                return False
            cur.execute(
                "INSERT INTO weekly_preferences (team_name, contact_person, team_size, preferred_days, submission_time) VALUES (%s, %s, %s, %s, NOW() AT TIME ZONE 'UTC')",
                (team, contact, size, days)
            )
            conn.commit()
            return True
    except psycopg2.Error as e:
        st.error(f"Database insert failed: {e}")
        conn.rollback()
        return False
    finally: return_connection(pool, conn)

def insert_oasis(pool, person, selected_days):
    if not pool: return False
    if not person:
        st.error("❌ Please enter your name.")
        return False
    if not 0 < len(selected_days) <= 5:
        st.error("❌ Select between 1 and 5 preferred days.")
        return False
    conn = get_connection(pool)
    if not conn: return False
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM oasis_preferences WHERE person_name = %s", (person,))
            if cur.fetchone():
                st.error("❌ You've already submitted. Contact admin to change your selection.")
                return False
            padded_days = selected_days + [None] * (5 - len(selected_days))
            cur.execute(
                "INSERT INTO oasis_preferences (person_name, preferred_day_1, preferred_day_2, preferred_day_3, preferred_day_4, preferred_day_5, submission_time) VALUES (%s, %s, %s, %s, %s, %s, NOW() AT TIME ZONE 'UTC')",
                (person.strip(), *padded_days)
            )
            conn.commit()
            return True
    except psycopg2.Error as e:
        st.error(f"Oasis insert failed: {e}")
        conn.rollback()
        return False
    finally: return_connection(pool, conn)

# -----------------------------------------------------
# Streamlit App UI
# -----------------------------------------------------
st.title("📅 Weekly Room Allocator")

st.info(
    """
    💡 **How This Works:**
    
    - 🧑‍🤝‍🧑 Project teams can select **either Monday & Wednesday** or **Tuesday & Thursday**. **Friday** is (for now) flexible. 
      There are 6 rooms for 4 persons and 1 room for 6 persons.
    - 🌿 Oasis users can choose **up to 5 preferred weekdays**, and will be randomly assigned—fairness is guaranteed. 
      There are 16 places in the Oasis.
    - ❗ You may only submit **once**. If you need to change your input, contact an admin.
    - 🗓️ **From Wednesday 09:00** you can submit your **project room preference** until **Thursday 16:00**. 
      The allocations will be shared on **Thursday at 16:00**.
    - 🌿 **Oasis preferences** can be submitted **from Wednesday 09:00 until Friday 16:00**, 
      and allocation will be done at **Friday 16:00**.
    - ✅ Allocations are refreshed **weekly** by an admin. 
        
    ---
    
    ### 🌿 Oasis: How to Join
    
    1. **✅ Reserve Oasis Seat (recommended)**  
       ➤ Submit your **preferred days** (up to 5).  
       ➤ Allocation is done **automatically and fairly** at **Friday 16:00**.  
       ➤ Everyone gets **at least one** of their preferred days, depending on availability.

    2. **⚠️ Add Yourself to Oasis Allocation (only if you forgot)**  
       ➤ Use this **only if you missed the deadline** or forgot to submit your preferences.  
       ➤ You will be added **immediately** to the selected days **if there’s space left**.  
       ➤ This option does **not guarantee fairness** and bypasses the regular process.

    ℹ️ Always use **"Reserve Oasis Seat"** before Friday 16:00 to ensure fair participation.  
    Only use **"Add Yourself"** if you forgot to register.
    """
)

now_local = datetime.now(OFFICE_TIMEZONE)
st.info(f"Current Office Time: **{now_local.strftime('%Y-%m-%d %H:%M:%S')}** ({OFFICE_TIMEZONE_STR})")

# ---------------- Admin Controls ---------------------
with st.expander("🔐 Admin Controls"):
    pwd = st.text_input("Enter admin password:", type="password", key="admin_pwd_main")

    if pwd == RESET_PASSWORD:
        st.success("✅ Access granted.")

        st.subheader("💼 Update Configurable Texts (for Submission Forms & General Info)")
        new_submission_week_of_text = st.text_input(
            "Text for 'Submissions for the week of ...' (e.g., '9 June')", 
            st.session_state["submission_week_of_text"],
            key="conf_sub_week_text"
        )
        new_sub_start_text = st.text_input(
            "Display text for 'Submission start'", 
            st.session_state["submission_start_text"],
            key="conf_sub_start_text"
        )
        new_sub_end_text = st.text_input(
            "Display text for 'Submission end'", 
            st.session_state["submission_end_text"],
            key="conf_sub_end_text"
        )
        new_oasis_end_text = st.text_input(
            "Display text for 'Oasis end'", 
            st.session_state["oasis_end_text"],
            key="conf_oasis_end_text"
        )
        
        new_project_alloc_display_markdown = st.text_input(
            "Text for 'Project Room Allocations' section header (can override auto-text)", 
            st.session_state["project_allocations_display_markdown_content"],
            key="conf_proj_alloc_header"
        )
        new_oasis_alloc_display_markdown = st.text_input(
            "Text for 'Oasis Allocations' section header (can override auto-text)", 
            st.session_state["oasis_allocations_display_markdown_content"],
            key="conf_oasis_alloc_header"
        )
        
        if st.button("Update All Configurable Texts", key="btn_update_conf_texts"):
            st.session_state["submission_week_of_text"] = new_submission_week_of_text
            st.session_state["submission_start_text"] = new_sub_start_text
            st.session_state["submission_end_text"] = new_sub_end_text
            st.session_state["oasis_end_text"] = new_oasis_end_text
            st.session_state["project_allocations_display_markdown_content"] = new_project_alloc_display_markdown
            st.session_state["oasis_allocations_display_markdown_content"] = new_oasis_alloc_display_markdown
            st.success("All configurable texts updated!")
            st.rerun()

        st.subheader("🧠 Project Room Admin")
        if st.button("🚀 Run Project Room Allocation", key="btn_run_proj_alloc"):
            if run_allocation:
                allocation_run_time = datetime.now(OFFICE_TIMEZONE) 
                # This will allocate for the week of allocation_run_time (e.g., actual current week)
                allocated_week_monday = allocation_run_time.date() - timedelta(days=allocation_run_time.date().weekday())
                
                success, _ = run_allocation(DATABASE_URL, only="project") # Assuming run_allocation uses current preferences for the current time's week

                if success:
                    # Update session state to reflect the week that was just allocated
                    st.session_state.project_rooms_display_monday = allocated_week_monday
                    new_submission_text = allocated_week_monday.strftime("%-d %B") 
                    st.session_state["submission_week_of_text"] = new_submission_text 
                    st.session_state["project_allocations_display_markdown_content"] = f"Displaying project rooms for the week of {allocated_week_monday.strftime('%-d %B %Y')}."
                    st.success(f"✅ Project room allocation completed. Project display updated to week of {allocated_week_monday.strftime('%Y-%m-%d')}.")
                    st.rerun()
                else:
                    st.error("❌ Project room allocation failed.")
            else:
                st.error("run_allocation function not available.")

        st.subheader("🌿 Oasis Admin")
        if st.button("🎲 Run Oasis Allocation", key="btn_run_oasis_alloc"):
            if run_allocation:
                allocation_run_time = datetime.now(OFFICE_TIMEZONE) 
                allocated_week_monday = allocation_run_time.date() - timedelta(days=allocation_run_time.date().weekday())

                success, _ = run_allocation(DATABASE_URL, only="oasis") 

                if success:
                    st.session_state.oasis_display_monday = allocated_week_monday
                    st.session_state["oasis_allocations_display_markdown_content"] = f"Displaying Oasis for the week of {allocated_week_monday.strftime('%-d %B %Y')}."
                    st.success(f"✅ Oasis allocation completed. Oasis display updated to week of {allocated_week_monday.strftime('%Y-%m-%d')}.")
                    st.rerun()
                else:
                    st.error("❌ Oasis allocation failed.")
            else:
                st.error("run_allocation function not available.")

        st.subheader("📌 Project Room Allocations (Admin Edit)")
        try:
            current_proj_display_mon = st.session_state.project_rooms_display_monday
            # st.markdown(f"*Editing project rooms for week: **{current_proj_display_mon.strftime('%Y-%m-%d')}***")
            alloc_df_admin = get_room_grid(pool, current_proj_display_mon) # Fetches for the week in session state
            if not alloc_df_admin.empty:
                editable_alloc_proj = st.data_editor(alloc_df_admin, num_rows="dynamic", use_container_width=True, key="edit_proj_allocations_data")
                if st.button("💾 Save Project Room Allocation Changes", key="btn_save_proj_alloc_changes"):
                    conn_admin_alloc = get_connection(pool)
                    if not conn_admin_alloc: st.error("No DB connection")
                    else:
                        try:
                            with conn_admin_alloc.cursor() as cur:
                                week_start_date = current_proj_display_mon # Use the displayed Monday
                                week_end_date = current_proj_display_mon + timedelta(days=3) # Mon-Thu
                                cur.execute("DELETE FROM weekly_allocations WHERE room_name != 'Oasis' AND date >= %s AND date <= %s", (week_start_date, week_end_date))
                                day_indices = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3}
                                for _, row in editable_alloc_proj.iterrows(): 
                                    for day_name, day_idx in day_indices.items():
                                        value = row.get(day_name, "")
                                        if value and value != "Vacant":
                                            team_info = str(value).split("(")[0].strip()
                                            room_name_val = str(row["Room"]) if pd.notnull(row["Room"]) else None
                                            alloc_date = current_proj_display_mon + timedelta(days=day_idx)
                                            if team_info and room_name_val:
                                                cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)", (team_info, room_name_val, alloc_date))
                            conn_admin_alloc.commit()
                            st.success(f"✅ Manual project room allocations updated for week of {current_proj_display_mon.strftime('%Y-%m-%d')}.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to save project room allocations: {e}")
                            if conn_admin_alloc: conn_admin_alloc.rollback()
                        finally: return_connection(pool, conn_admin_alloc)
            else:
                st.info(f"No project room allocations for week of {current_proj_display_mon.strftime('%Y-%m-%d')} to edit (or data is vacant).")
        except Exception as e:
            st.warning(f"Failed to load project room allocation data for admin edit: {e}")

        st.subheader("🧹 Reset Project Room Data")
        proj_reset_week_text = st.session_state.project_rooms_display_monday.strftime('%Y-%m-%d')
        if st.button(f"🗑️ Remove Project Allocations for Displayed Week ({proj_reset_week_text})", key="btn_reset_proj_alloc_week"):
            conn_reset_pra = get_connection(pool)
            if conn_reset_pra:
                try:
                    with conn_reset_pra.cursor() as cur:
                        mon_to_reset = st.session_state.project_rooms_display_monday
                        cur.execute("DELETE FROM weekly_allocations WHERE room_name != 'Oasis' AND date >= %s AND date <= %s", (mon_to_reset, mon_to_reset + timedelta(days=6))) # Clear for the full week Mon-Sun
                        conn_reset_pra.commit()
                        st.success(f"✅ Project room allocations (non-Oasis) removed for week of {mon_to_reset.strftime('%Y-%m-%d')}.")
                        st.rerun()
                except Exception as e: st.error(f"❌ Failed to reset project allocations: {e}"); conn_reset_pra.rollback()
                finally: return_connection(pool, conn_reset_pra)

        if st.button("🧽 Remove All Project Room Preferences (Global Action)", key="btn_reset_all_proj_prefs"):
            # Added a confirm checkbox for safety, as this is a destructive global action
            confirm_prp_reset = st.checkbox("Confirm removal of ALL project room preferences?", key="chk_confirm_prp_reset_main")
            if confirm_prp_reset:
                conn_reset_prp = get_connection(pool)
                if conn_reset_prp:
                    try:
                        with conn_reset_prp.cursor() as cur:
                            cur.execute("DELETE FROM weekly_preferences")
                            conn_reset_prp.commit()
                            st.success("✅ All project room preferences removed.")
                            st.rerun()
                    except Exception as e: st.error(f"❌ Failed: {e}"); conn_reset_prp.rollback()
                    finally: return_connection(pool, conn_reset_prp)


        st.subheader("🌾 Reset Oasis Data")
        oasis_reset_week_text = st.session_state.oasis_display_monday.strftime('%Y-%m-%d')
        if st.button(f"🗑️ Remove Oasis Allocations for Displayed Week ({oasis_reset_week_text})", key="btn_reset_oasis_alloc_week"):
            conn_reset_oa = get_connection(pool)
            if conn_reset_oa:
                try:
                    with conn_reset_oa.cursor() as cur:
                        mon_to_reset = st.session_state.oasis_display_monday
                        cur.execute("DELETE FROM weekly_allocations WHERE room_name = 'Oasis' AND date >= %s AND date <= %s", (mon_to_reset, mon_to_reset + timedelta(days=6))) # Clear for the full week Mon-Sun
                        conn_reset_oa.commit()
                        st.success(f"✅ Oasis allocations removed for week of {mon_to_reset.strftime('%Y-%m-%d')}.")
                        st.rerun()
                except Exception as e: st.error(f"❌ Failed to reset Oasis allocations: {e}"); conn_reset_oa.rollback()
                finally: return_connection(pool, conn_reset_oa)
        
        if st.button("🧽 Remove All Oasis Preferences (Global Action)", key="btn_reset_all_oasis_prefs"):
            # Added a confirm checkbox for safety
            confirm_op_reset = st.checkbox("Confirm removal of ALL Oasis preferences?", key="chk_confirm_op_reset_main")
            if confirm_op_reset:
                conn_reset_op = get_connection(pool)
                if conn_reset_op:
                    try:
                        with conn_reset_op.cursor() as cur:
                            cur.execute("DELETE FROM oasis_preferences")
                            conn_reset_op.commit()
                            st.success("✅ All Oasis preferences removed.")
                            st.rerun()
                    except Exception as e: st.error(f"❌ Failed: {e}"); conn_reset_op.rollback()
                    finally: return_connection(pool, conn_reset_op)

        st.subheader("🧾 Team Preferences (Admin Edit - Global)")
        df_team_prefs_admin = get_preferences(pool)
        if not df_team_prefs_admin.empty:
            editable_team_df = st.data_editor(df_team_prefs_admin, num_rows="dynamic", use_container_width=True, key="edit_teams_prefs_data")
            if st.button("💾 Save Team Preference Changes", key="btn_save_team_prefs_changes"):
                conn_admin_tp = get_connection(pool)
                if conn_admin_tp:
                    try:
                        with conn_admin_tp.cursor() as cur:
                            cur.execute("DELETE FROM weekly_preferences")
                            for _, row in editable_team_df.iterrows():
                                sub_time = row.get("Submitted At", datetime.now(pytz.utc))
                                if pd.isna(sub_time) or sub_time is None: sub_time = datetime.now(pytz.utc)
                                cur.execute("INSERT INTO weekly_preferences (team_name, contact_person, team_size, preferred_days, submission_time) VALUES (%s, %s, %s, %s, %s)",
                                            (row["Team"], row["Contact"], int(row["Size"]), row["Days"], sub_time) )
                            conn_admin_tp.commit(); st.success("✅ Team preferences updated."); st.rerun()
                    except Exception as e: st.error(f"❌ Failed to update team preferences: {e}"); conn_admin_tp.rollback()
                    finally: return_connection(pool, conn_admin_tp)
        else: st.info("No team preferences submitted yet to edit.")

        st.subheader("🌿 Oasis Preferences (Admin Edit - Global)")
        df_oasis_prefs_admin = get_oasis_preferences(pool)
        if not df_oasis_prefs_admin.empty:
            cols_to_display = ["Person", "Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Submitted At"]
            editable_oasis_df_prefs = st.data_editor(df_oasis_prefs_admin[cols_to_display], num_rows="dynamic", use_container_width=True, key="edit_oasis_prefs_data")
            if st.button("💾 Save Oasis Preference Changes", key="btn_save_oasis_prefs_changes"):
                conn_admin_op = get_connection(pool)
                if conn_admin_op:
                    try:
                        with conn_admin_op.cursor() as cur:
                            cur.execute("DELETE FROM oasis_preferences")
                            for _, row in editable_oasis_df_prefs.iterrows():
                                sub_time = row.get("Submitted At", datetime.now(pytz.utc))
                                if pd.isna(sub_time) or sub_time is None: sub_time = datetime.now(pytz.utc)
                                cur.execute("INSERT INTO oasis_preferences (person_name, preferred_day_1, preferred_day_2, preferred_day_3, preferred_day_4, preferred_day_5, submission_time) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                                            (row["Person"], row.get("Day 1"), row.get("Day 2"), row.get("Day 3"), row.get("Day 4"), row.get("Day 5"), sub_time))
                            conn_admin_op.commit(); st.success("✅ Oasis preferences updated."); st.rerun()
                    except Exception as e: st.error(f"❌ Failed to update oasis preferences: {e}"); conn_admin_op.rollback()
                    finally: return_connection(pool, conn_admin_op)
        else: st.info("No oasis preferences submitted yet to edit.")

    elif pwd: 
        st.error("❌ Incorrect password.")

# -----------------------------------------------------
# Team Form (Project Room Requests)
# -----------------------------------------------------
st.header("📝 Request Project Room")
st.markdown(
    f"""
    For teams of 3 or more. Submissions for the **week of {st.session_state["submission_week_of_text"]}** are open 
    from **{st.session_state["submission_start_text"]}** until **{st.session_state["submission_end_text"]}**.
    """
)
with st.form("team_form_main"):
    team_name = st.text_input("Team Name", key="tf_team_name")
    contact_person = st.text_input("Contact Person", key="tf_contact_person")
    team_size = st.number_input("Team Size (3-6)", min_value=3, max_value=6, value=3, key="tf_team_size")
    day_choice = st.selectbox("Preferred Days", ["Monday and Wednesday", "Tuesday and Thursday"], key="tf_day_choice")
    submit_team_pref = st.form_submit_button("Submit Project Room Request")

    if submit_team_pref:
        day_map = {
            "Monday and Wednesday": "Monday,Wednesday",
            "Tuesday and Thursday": "Tuesday,Thursday"
        }
        if insert_preference(pool, team_name, contact_person, team_size, day_map[day_choice]):
            st.success(f"✅ Preference submitted for {team_name}!")
            st.rerun()

# -----------------------------------------------------
# Oasis Form (Preferences)
# -----------------------------------------------------
st.header("🌿 Reserve Oasis Seat")
st.markdown(
    f"""
    Submit your personal preferences for the **week of {st.session_state["submission_week_of_text"]}**. 
    Submissions open from **{st.session_state["submission_start_text"]}** until **{st.session_state["oasis_end_text"]}**.
    """
)
with st.form("oasis_form_main"):
    oasis_person_name = st.text_input("Your Name", key="of_oasis_person")
    oasis_selected_days = st.multiselect(
        "Select Your Preferred Days for Oasis (up to 5):",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        max_selections=5,
        key="of_oasis_days"
    )
    submit_oasis_pref = st.form_submit_button("Submit Oasis Preference")

    if submit_oasis_pref:
        if insert_oasis(pool, oasis_person_name, oasis_selected_days):
            st.success(f"✅ Oasis preference submitted for {oasis_person_name}!")
            st.rerun()

# -----------------------------------------------------
# Display: Project Room Allocations
# -----------------------------------------------------
st.header("📌 Project Room Allocations")
st.markdown(st.session_state['project_allocations_display_markdown_content']) 
alloc_display_df = get_room_grid(pool, st.session_state.project_rooms_display_monday) 
if alloc_display_df.empty:
    st.write(f"No project room allocations yet for the week of {st.session_state.project_rooms_display_monday.strftime('%d %B %Y')} (or data is vacant).")
else:
    st.dataframe(alloc_display_df, use_container_width=True, hide_index=True)

# -----------------------------------------------------
# Ad-hoc Oasis Addition
# -----------------------------------------------------
st.header("🚶 Add Yourself to Oasis (Ad-hoc)")
current_oasis_display_mon_adhoc = st.session_state.oasis_display_monday 
st.caption(f"Use this if you missed preference submission. Subject to availability for week of {current_oasis_display_mon_adhoc.strftime('%d %B %Y')}.") # Added week display
with st.form("oasis_add_form_main"):
    adhoc_oasis_name = st.text_input("Your Name", key="af_adhoc_name")
    adhoc_oasis_days = st.multiselect(
        f"Select day(s) for week of {current_oasis_display_mon_adhoc.strftime('%d %B')}:", # Added week display
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
        key="af_adhoc_days"
    )
    add_adhoc_submit = st.form_submit_button("➕ Add Me to Oasis Schedule")

    if add_adhoc_submit:
        if not adhoc_oasis_name.strip(): st.error("❌ Please enter your name.")
        elif not adhoc_oasis_days: st.error("❌ Select at least one day.")
        else:
            conn_adhoc = get_connection(pool)
            if not conn_adhoc: st.error("No DB Connection")
            else:
                try:
                    with conn_adhoc.cursor() as cur:
                        name_clean = adhoc_oasis_name.strip().title()
                        days_map_indices = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4}
                        
                        # First, remove any existing ad-hoc entries for this person on these days to prevent duplicates if re-adding
                        for day_str in adhoc_oasis_days: 
                            date_obj_check = current_oasis_display_mon_adhoc + timedelta(days=days_map_indices[day_str])
                            cur.execute("DELETE FROM weekly_allocations WHERE room_name = 'Oasis' AND team_name = %s AND date = %s", (name_clean, date_obj_check))
                        
                        added_to_all_selected = True
                        any_added = False
                        for day_str in adhoc_oasis_days:
                            date_obj = current_oasis_display_mon_adhoc + timedelta(days=days_map_indices[day_str])
                            cur.execute("SELECT COUNT(*) FROM weekly_allocations WHERE room_name = 'Oasis' AND date = %s", (date_obj,))
                            count = cur.fetchone()[0]
                            if count >= oasis.get("capacity", 15):
                                st.warning(f"⚠️ Oasis is full on {day_str} ({date_obj.strftime('%d %B')}). Could not add {name_clean}.")
                                added_to_all_selected = False
                            else:
                                cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, 'Oasis', %s)", (name_clean, date_obj))
                                any_added = True
                        conn_adhoc.commit()

                        if any_added and added_to_all_selected:
                            st.success(f"✅ {name_clean} added to Oasis for selected day(s) in week of {current_oasis_display_mon_adhoc.strftime('%d %B')}!")
                        elif any_added: # Partially added
                            st.info(f"ℹ️ {name_clean} added to Oasis for some selected day(s) in week of {current_oasis_display_mon_adhoc.strftime('%d %B')}. Check warnings above for full days.")
                        elif not adhoc_oasis_days: # Should be caught by earlier check, but as a safeguard
                             st.error("❌ No days were selected.")
                        else: # Not added to any, all were full or other issue
                            st.error(f"❌ Could not add {name_clean} to Oasis for any selected days in week of {current_oasis_display_mon_adhoc.strftime('%d %B')}. All may be full.")
                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error adding to Oasis: {e}")
                    if conn_adhoc: conn_adhoc.rollback()
                finally: return_connection(pool, conn_adhoc)

# -----------------------------------------------------
# Full Weekly Oasis Overview
# -----------------------------------------------------
st.header("📊 Full Weekly Oasis Overview")
st.markdown(st.session_state['oasis_allocations_display_markdown_content']) 
oasis_overview_monday_display = st.session_state.oasis_display_monday 
oasis_overview_days_dates = [oasis_overview_monday_display + timedelta(days=i) for i in range(5)]
oasis_overview_day_names = [d.strftime("%A (%-d %b)") for d in oasis_overview_days_dates] # Added date to day name
oasis_capacity = oasis.get("capacity", 15)

conn_matrix = get_connection(pool)
if not conn_matrix: st.error("No DB connection for Oasis Overview")
else:
    try:
        with conn_matrix.cursor() as cur:
            cur.execute( 
                "SELECT team_name, date FROM weekly_allocations WHERE room_name = 'Oasis' AND date >= %s AND date <= %s",
                (oasis_overview_monday_display, oasis_overview_days_dates[-1])
            )
            rows = cur.fetchall()

        df_matrix_data = pd.DataFrame(rows, columns=["Name", "Date"]) if rows else pd.DataFrame(columns=["Name", "Date"])
        if not df_matrix_data.empty:
            df_matrix_data["Date"] = pd.to_datetime(df_matrix_data["Date"]).dt.date

        unique_names_allocated = set(df_matrix_data["Name"]) if not df_matrix_data.empty else set()
        names_from_prefs = set()
        try: 
            with conn_matrix.cursor() as cur: 
                cur.execute("SELECT DISTINCT person_name FROM oasis_preferences")
                pref_rows = cur.fetchall()
                names_from_prefs = {row[0] for row in pref_rows}
        except psycopg2.Error: st.warning("Could not fetch names from Oasis preferences for matrix display.")
        
        # Ensure 'Niek' (or any placeholder/always-present user) is handled correctly if needed
        # If 'Niek' is just an example user, this union might not be necessary unless Niek can exist outside of preferences/allocations.
        all_relevant_names = sorted(list(unique_names_allocated.union(names_from_prefs))) 
        if not all_relevant_names and "Niek" in AVAILABLE_ROOMS: # Assuming Niek is a special case that should always appear
             all_relevant_names = ["Niek"] # Or handle Niek separately if Niek's presence is conditional
        elif "Niek" not in all_relevant_names and "Niek" in AVAILABLE_ROOMS: # If Niek should be there but isn't from data
            all_relevant_names.append("Niek")
            all_relevant_names.sort()
        
        if not all_relevant_names: # If still no names (e.g. Niek isn't a factor)
            st.write(f"No Oasis preferences or allocations for the week of {oasis_overview_monday_display.strftime('%d %B %Y')}.")
            # Raise st.stop() or return to prevent further processing if df will be empty and cause errors
            # For now, let it proceed, an empty editor might be fine.
            initial_matrix_df = pd.DataFrame(columns=oasis_overview_day_names) # Empty dataframe
        else:
            initial_matrix_df = pd.DataFrame(False, index=all_relevant_names, columns=oasis_overview_day_names)

            if not df_matrix_data.empty: 
                for _, row_data in df_matrix_data.iterrows():
                    person_name = row_data["Name"]
                    alloc_date = row_data["Date"]
                    if alloc_date in oasis_overview_days_dates and person_name in initial_matrix_df.index:
                        initial_matrix_df.at[person_name, alloc_date.strftime("%A (%-d %b)")] = True # Match column name
            
            # Example: if Niek is always present and allocated every day by default (adjust if this is not the case)
            # if "Niek" in initial_matrix_df.index: 
            #     for day_n_col in oasis_overview_day_names: initial_matrix_df.at["Niek", day_n_col] = True
        
        st.subheader("🪑 Oasis Availability Summary")
        current_day_alloc_counts = {day_dt: 0 for day_dt in oasis_overview_days_dates}
        if not df_matrix_data.empty:
            for day_dt_check in oasis_overview_days_dates:
                # Count unique names for the specific date
                current_day_alloc_counts[day_dt_check] = df_matrix_data[df_matrix_data["Date"] == day_dt_check]["Name"].nunique()
        
        cols_summary = st.columns(len(oasis_overview_day_names))
        for idx, day_dt_s in enumerate(oasis_overview_days_dates):
            day_str_label_s = day_dt_s.strftime("%A (%-d %b)")
            used_spots = current_day_alloc_counts[day_dt_s]
            spots_left = max(0, oasis_capacity - used_spots)
            with cols_summary[idx]:
                 st.metric(label=day_str_label_s, value=f"{spots_left}", delta=f"{used_spots} used", delta_color="off")


        # Only show editor if there's data to edit
        if not initial_matrix_df.empty:
            edited_matrix = st.data_editor(
                initial_matrix_df, 
                use_container_width=True,
                disabled=["Niek"] if "Niek" in initial_matrix_df.index and "Niek" in AVAILABLE_ROOMS else [], # Example of disabling Niek
                key="oasis_matrix_editor_main"
            )

            if st.button("💾 Save Oasis Matrix Changes", key="btn_save_oasis_matrix_changes"):
                try:
                    with conn_matrix.cursor() as cur:
                        # Clear existing Oasis allocations for the week for users in the matrix (excluding special cases if any)
                        # Be careful with blanket deletes if 'Niek' or others have special handling
                        names_in_matrix = edited_matrix.index.tolist()
                        placeholders = ', '.join(['%s'] * len(names_in_matrix))
                        
                        # More targeted delete: only for people in the current matrix view for the current week
                        cur.execute(f"""DELETE FROM weekly_allocations 
                                      WHERE room_name = 'Oasis' 
                                      AND team_name IN ({placeholders})
                                      AND date >= %s AND date <= %s""", 
                                   names_in_matrix + [oasis_overview_monday_display, oasis_overview_days_dates[-1]])

                        occupied_counts_per_day = {day_col: 0 for day_col in oasis_overview_day_names}
                        
                        # Recalculate Niek's contribution if Niek is special and always there
                        # if "Niek" in edited_matrix.index and "Niek" in AVAILABLE_ROOMS: # Assuming Niek is a special always-present user
                        #     for day_idx, day_col_name in enumerate(oasis_overview_day_names):
                        #         if edited_matrix.at["Niek", day_col_name]: # if Niek can be toggled
                        #             occupied_counts_per_day[day_col_name] +=1


                        for person_name_matrix in edited_matrix.index: 
                            # if person_name_matrix == "Niek" and "Niek" in AVAILABLE_ROOMS: continue # Skip Niek if handled separately or always true
                            for day_idx, day_col_name in enumerate(oasis_overview_day_names): # day_col_name is "Monday (02 Jun)"
                                if edited_matrix.at[person_name_matrix, day_col_name]: 
                                    current_date_for_col = oasis_overview_days_dates[day_idx] # Get the actual date object
                                    if occupied_counts_per_day[day_col_name] < oasis_capacity:
                                        cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)", 
                                                    (person_name_matrix, "Oasis", current_date_for_col))
                                        occupied_counts_per_day[day_col_name] += 1
                                    else:
                                        st.warning(f"⚠️ {person_name_matrix} could not be added to Oasis on {day_col_name}: capacity ({oasis_capacity}) reached.")
                                        
                        conn_matrix.commit()
                        st.success("✅ Oasis Matrix saved successfully!")
                        st.rerun()
                except Exception as e_matrix_save:
                    st.error(f"❌ Failed to save Oasis Matrix: {e_matrix_save}")
                    if conn_matrix: conn_matrix.rollback()
        else:
            st.write("No data to display or edit in the Oasis Matrix for this week.") # Message if initial_matrix_df is empty

    except Exception as e_matrix_load:
        st.error(f"❌ Error loading Oasis Matrix data: {e_matrix_load}")
    finally: return_connection(pool, conn_matrix)

# -----------------------------------------------------
# Final Note: DB connectivity check
# -----------------------------------------------------
if not pool:
    st.error("🚨 Cannot connect to the database. Please check configurations or contact an admin.")