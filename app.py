import streamlit as st
import psycopg2
import psycopg2.pool
import json
import os
from datetime import datetime, timedelta, date
import pytz
import pandas as pd
from psycopg2.extras import RealDictCursor

# Placeholder for run_allocation if the file is not available
# If you have a valid allocate_rooms.py, you would use:
# from allocate_rooms import run_allocation
# IMPORTANT: The real run_allocation function needs to use the 'allocated_week_monday'
# passed to it to determine which week to process.
def run_allocation(db_url, allocated_week_monday: date, only=None):
    st.warning(f"Placeholder: run_allocation called for {only} for week starting {allocated_week_monday.strftime('%Y-%m-%d')}. Implement actual logic to process this specific week.")
    # Simulate success for testing UI flow
    # In a real scenario, this function would query preferences and write allocations
    # for the 'allocated_week_monday'.
    return True, f"Placeholder allocation successful for {allocated_week_monday.strftime('%Y-%m-%d')}"


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
    try:
        return psycopg2.pool.SimpleConnectionPool(1, 25, dsn=DATABASE_URL)
    except psycopg2.OperationalError as e:
        st.error(f"Failed to connect to database: {e}")
        return None


def get_connection(pool):
    if pool: return pool.getconn()
    return None

def return_connection(pool, conn):
    if pool and conn: pool.putconn(conn)

pool = get_db_connection_pool()

# -----------------------------------------------------
# Helper to load/update display dates and UI texts
# -----------------------------------------------------

initial_proj_date_str = st.query_params.get("proj_date")
initial_oasis_date_str = st.query_params.get("oasis_date")

parsed_proj_date = None
if initial_proj_date_str:
    try:
        parsed_proj_date = datetime.strptime(initial_proj_date_str, "%Y-%m-%d").date()
    except ValueError:
        st.warning(f"Invalid project date in URL: {initial_proj_date_str}. Defaulting.")
        parsed_proj_date = None

parsed_oasis_date = None
if initial_oasis_date_str:
    try:
        parsed_oasis_date = datetime.strptime(initial_oasis_date_str, "%Y-%m-%d").date()
    except ValueError:
        st.warning(f"Invalid oasis date in URL: {initial_oasis_date_str}. Defaulting.")
        parsed_oasis_date = None

now_in_tz_init = datetime.now(OFFICE_TIMEZONE)
current_week_monday_init = now_in_tz_init.date() - timedelta(days=now_in_tz_init.date().weekday())

st.session_state.project_rooms_display_monday = parsed_proj_date or st.session_state.get("project_rooms_display_monday", current_week_monday_init)
st.session_state.oasis_display_monday = parsed_oasis_date or st.session_state.get("oasis_display_monday", current_week_monday_init)


default_submission_week_of_text = st.session_state.project_rooms_display_monday.strftime("%-d %B")
if "submission_week_of_text" not in st.session_state or parsed_proj_date :
    st.session_state["submission_week_of_text"] = default_submission_week_of_text

if "submission_start_text" not in st.session_state:
    st.session_state["submission_start_text"] = "Wednesday 4 June 09:00" # Example, should be configurable
if "submission_end_text" not in st.session_state:
    st.session_state["submission_end_text"] = "Thursday 5 June 16:00" # Example
if "oasis_end_text" not in st.session_state:
    st.session_state["oasis_end_text"] = "Friday 6 June 16:00" # Example

default_project_alloc_markdown = f"Displaying project rooms for the week of {st.session_state.project_rooms_display_monday.strftime('%-d %B %Y')}."
if "project_allocations_display_markdown_content" not in st.session_state or parsed_proj_date:
    st.session_state["project_allocations_display_markdown_content"] = default_project_alloc_markdown

default_oasis_alloc_markdown = f"Displaying Oasis for the week of {st.session_state.oasis_display_monday.strftime('%-d %B %Y')}."
if "oasis_allocations_display_markdown_content" not in st.session_state or parsed_oasis_date:
    st.session_state["oasis_allocations_display_markdown_content"] = default_oasis_alloc_markdown


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
        with open(ROOMS_FILE, 'r') as f: all_rooms = [r["name"] for r in json.load(f) if r["name"] != "Oasis"]
    except (FileNotFoundError, json.JSONDecodeError):
        st.error(f"Error: Could not load valid data from {ROOMS_FILE}.")
        return pd.DataFrame(columns=["Room"] + day_labels)
    
    grid = {room: {**{"Room": room}, **{day: "Vacant" for day in day_labels}} for room in all_rooms}
    if not all_rooms: 
        return pd.DataFrame(columns=["Room"] + day_labels)

    conn = get_connection(pool)
    if not conn: return pd.DataFrame(list(grid.values()) if grid else columns=["Room"] + day_labels) #MODIFIED
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
        return pd.DataFrame(list(grid.values()))
    except psycopg2.Error as e:
        st.warning(f"Database error while getting room grid: {e}")
        return pd.DataFrame(list(grid.values()) if grid else columns=["Room"] + day_labels) #MODIFIED
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
        if conn: conn.rollback()
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
        if conn: conn.rollback()
        return False
    finally: return_connection(pool, conn)

# -----------------------------------------------------
# Streamlit App UI
# -----------------------------------------------------
st.title("📅 Weekly Room Allocator")

st.info(
    """
    💡 **How This Works:**
    
    - 🧑‍🤝‍🧑 Project teams select preferred days. Allocations aim for these days.
    - 🌿 Oasis users pick preferred days. Allocation is fair, based on availability.
    - ❗ Submissions are typically once per week. Contact admin for changes.
    - 🗓️ **Project room preferences**: Submissions open based on admin-set times. Allocations are then run by an admin.
    - 🌿 **Oasis preferences**: Similar submission window, admin runs allocation.
    - ✅ Allocations are run by an admin for the displayed week.
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
        # ... (configurable text inputs remain the same) ...
        current_s_week_of_text = st.session_state.get("submission_week_of_text", default_submission_week_of_text)
        new_submission_week_of_text = st.text_input(
            "Text for 'Submissions for the week of ...' (e.g., '9 June')",
            current_s_week_of_text,
            key="conf_sub_week_text"
        )
        new_sub_start_text = st.text_input(
            "Display text for 'Submission start'",
            st.session_state.get("submission_start_text", "Wednesday 4 June 09:00"),
            key="conf_sub_start_text"
        )
        new_sub_end_text = st.text_input(
            "Display text for 'Submission end'",
            st.session_state.get("submission_end_text", "Thursday 5 June 16:00"),
            key="conf_sub_end_text"
        )
        new_oasis_end_text = st.text_input(
            "Display text for 'Oasis end'",
            st.session_state.get("oasis_end_text", "Friday 6 June 16:00"),
            key="conf_oasis_end_text"
        )
        
        current_proj_alloc_md = st.session_state.get("project_allocations_display_markdown_content", default_project_alloc_markdown)
        new_project_alloc_display_markdown = st.text_area(
            "Text for 'Project Room Allocations' section header (can override auto-text)",
            current_proj_alloc_md,
            key="conf_proj_alloc_header"
        )
        
        current_oasis_alloc_md = st.session_state.get("oasis_allocations_display_markdown_content", default_oasis_alloc_markdown)
        new_oasis_alloc_display_markdown = st.text_area(
            "Text for 'Oasis Allocations' section header (can override auto-text)",
            current_oasis_alloc_md,
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


        st.subheader("🗓️ Set Display Dates (Persists in URL)")
        admin_selected_project_display_date = st.date_input(
            "Set Project Rooms Display Week Starting Monday:",
            value=st.session_state.project_rooms_display_monday,
            help="Select any date; it will be adjusted to Monday. This will update the URL.",
            key="admin_set_project_display_date_url"
        )
        admin_selected_oasis_display_date = st.date_input(
            "Set Oasis Display Week Starting Monday:",
            value=st.session_state.oasis_display_monday,
            help="Select any date; it will be adjusted to Monday. This will update the URL.",
            key="admin_set_oasis_display_date_url"
        )

        if st.button("Update Display Weeks & Refresh", key="btn_update_display_weeks_url"):
            final_project_monday = admin_selected_project_display_date - timedelta(days=admin_selected_project_display_date.weekday())
            final_oasis_monday = admin_selected_oasis_display_date - timedelta(days=admin_selected_oasis_display_date.weekday())

            st.session_state.project_rooms_display_monday = final_project_monday
            st.session_state.oasis_display_monday = final_oasis_monday
            st.session_state["project_allocations_display_markdown_content"] = f"Displaying project rooms for the week of {final_project_monday.strftime('%-d %B %Y')}."
            st.session_state["oasis_allocations_display_markdown_content"] = f"Displaying Oasis for the week of {final_oasis_monday.strftime('%-d %B %Y')}."
            st.session_state["submission_week_of_text"] = final_project_monday.strftime("%-d %B")
            
            st.query_params = {
                "proj_date": final_project_monday.strftime("%Y-%m-%d"),
                "oasis_date": final_oasis_monday.strftime("%Y-%m-%d")
            }
            st.success(f"Display weeks set in URL. Project rooms: {final_project_monday.strftime('%Y-%m-%d')}, Oasis: {final_oasis_monday.strftime('%Y-%m-%d')}. Page will now refresh.")
            st.rerun()

        st.subheader("🧠 Project Room Admin")
        if st.button("🚀 Run Project Room Allocation", key="btn_run_proj_alloc"):
            if 'run_allocation' in globals() and callable(run_allocation):
                # MODIFIED: Use the currently displayed project week for allocation
                allocated_week_monday = st.session_state.project_rooms_display_monday
                
                success, message = run_allocation(DATABASE_URL, allocated_week_monday=allocated_week_monday, only="project")

                if success:
                    # The display is already set to this week, so no need to change session_state for dates.
                    # Update markdown and submission text to be sure they reflect the processed week.
                    st.session_state["submission_week_of_text"] = allocated_week_monday.strftime("%-d %B")
                    st.session_state["project_allocations_display_markdown_content"] = f"Displaying project rooms for the week of {allocated_week_monday.strftime('%-d %B %Y')}."
                    # Ensure URL reflects the week processed, if it changed (though it shouldn't in this flow)
                    st.query_params["proj_date"] = allocated_week_monday.strftime("%Y-%m-%d")
                    st.success(f"✅ Project room allocation completed for week of {allocated_week_monday.strftime('%Y-%m-%d')}. {message}")
                    st.rerun()
                else:
                    st.error(f"❌ Project room allocation failed for week of {allocated_week_monday.strftime('%Y-%m-%d')}. {message}")
            else:
                st.error("run_allocation function not available. Please ensure allocate_rooms.py is correctly set up if used.")

        st.subheader("🌿 Oasis Admin")
        if st.button("🎲 Run Oasis Allocation", key="btn_run_oasis_alloc"):
            if 'run_allocation' in globals() and callable(run_allocation):
                # MODIFIED: Use the currently displayed oasis week for allocation
                allocated_week_monday = st.session_state.oasis_display_monday

                success, message = run_allocation(DATABASE_URL, allocated_week_monday=allocated_week_monday, only="oasis")

                if success:
                    st.session_state["oasis_allocations_display_markdown_content"] = f"Displaying Oasis for the week of {allocated_week_monday.strftime('%-d %B %Y')}."
                    # Ensure URL reflects the week processed
                    st.query_params["oasis_date"] = allocated_week_monday.strftime("%Y-%m-%d")
                    st.success(f"✅ Oasis allocation completed for week of {allocated_week_monday.strftime('%Y-%m-%d')}. {message}")
                    st.rerun()
                else:
                    st.error(f"❌ Oasis allocation failed for week of {allocated_week_monday.strftime('%Y-%m-%d')}. {message}")
            else:
                st.error("run_allocation function not available. Please ensure allocate_rooms.py is correctly set up if used.")

        # ... (Rest of the admin controls: Admin Edit, Resets remain largely the same) ...
        st.subheader("📌 Project Room Allocations (Admin Edit)")
        try:
            current_proj_display_mon = st.session_state.project_rooms_display_monday
            alloc_df_admin = get_room_grid(pool, current_proj_display_mon)
            if not alloc_df_admin.empty:
                editable_alloc_proj = st.data_editor(alloc_df_admin, num_rows="dynamic", use_container_width=True, key="edit_proj_allocations_data")
                if st.button("💾 Save Project Room Allocation Changes", key="btn_save_proj_alloc_changes"):
                    conn_admin_alloc = get_connection(pool)
                    if not conn_admin_alloc: st.error("No DB connection")
                    else:
                        try:
                            with conn_admin_alloc.cursor() as cur:
                                week_start_date = current_proj_display_mon
                                week_end_date = current_proj_display_mon + timedelta(days=3)
                                cur.execute("DELETE FROM weekly_allocations WHERE room_name != 'Oasis' AND date >= %s AND date <= %s", (week_start_date, week_end_date))
                                day_indices = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3}
                                for _, row in editable_alloc_proj.iterrows():
                                    room_name_val = str(row["Room"]) if pd.notnull(row["Room"]) else None
                                    if not room_name_val: continue

                                    for day_name, day_idx in day_indices.items():
                                        value = row.get(day_name, "")
                                        if value and value != "Vacant":
                                            team_info = str(value).split("(")[0].strip()
                                            alloc_date = current_proj_display_mon + timedelta(days=day_idx)
                                            if team_info:
                                                cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)", (team_info, room_name_val, alloc_date))
                            conn_admin_alloc.commit()
                            st.success(f"✅ Manual project room allocations updated for week of {current_proj_display_mon.strftime('%Y-%m-%d')}.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to save project room allocations: {e}")
                            if conn_admin_alloc: conn_admin_alloc.rollback()
                        finally: return_connection(pool, conn_admin_alloc)
            else:
                st.info(f"No project room allocations for week of {current_proj_display_mon.strftime('%Y-%m-%d')} to edit, or data is empty.")
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
                        cur.execute("DELETE FROM weekly_allocations WHERE room_name != 'Oasis' AND date >= %s AND date <= %s", (mon_to_reset, mon_to_reset + timedelta(days=3)))
                        conn_reset_pra.commit()
                        st.success(f"✅ Project room allocations (non-Oasis) removed for week of {mon_to_reset.strftime('%Y-%m-%d')}.")
                        st.rerun()
                except Exception as e: st.error(f"❌ Failed to reset project allocations: {e}"); conn_reset_pra.rollback()
                finally: return_connection(pool, conn_reset_pra)

        if st.button("🧽 Remove All Project Room Preferences (Global Action)", key="btn_reset_all_proj_prefs_confirmable"):
            st.session_state.confirm_prp_reset = True
        
        if st.session_state.get("confirm_prp_reset"):
            st.warning("⚠️ Are you sure you want to remove ALL project room preferences? This cannot be undone.")
            col1_prp, col2_prp = st.columns(2)
            with col1_prp:
                if st.button("YES, DELETE ALL PROJECT PREFERENCES", key="btn_confirm_delete_prp_yes"):
                    conn_reset_prp = get_connection(pool)
                    if conn_reset_prp:
                        try:
                            with conn_reset_prp.cursor() as cur:
                                cur.execute("DELETE FROM weekly_preferences")
                                conn_reset_prp.commit()
                                st.success("✅ All project room preferences removed.")
                                st.session_state.confirm_prp_reset = False 
                                st.rerun()
                        except Exception as e: st.error(f"❌ Failed: {e}"); conn_reset_prp.rollback()
                        finally: return_connection(pool, conn_reset_prp)
            with col2_prp:
                if st.button("NO, CANCEL PROJECT PREFERENCES DELETION", key="btn_confirm_delete_prp_no"):
                    st.session_state.confirm_prp_reset = False
                    st.rerun()

        st.subheader("🌾 Reset Oasis Data")
        oasis_reset_week_text = st.session_state.oasis_display_monday.strftime('%Y-%m-%d')
        if st.button(f"🗑️ Remove Oasis Allocations for Displayed Week ({oasis_reset_week_text})", key="btn_reset_oasis_alloc_week"):
            conn_reset_oa = get_connection(pool)
            if conn_reset_oa:
                try:
                    with conn_reset_oa.cursor() as cur:
                        mon_to_reset = st.session_state.oasis_display_monday
                        cur.execute("DELETE FROM weekly_allocations WHERE room_name = 'Oasis' AND date >= %s AND date <= %s", (mon_to_reset, mon_to_reset + timedelta(days=4)))
                        conn_reset_oa.commit()
                        st.success(f"✅ Oasis allocations removed for week of {mon_to_reset.strftime('%Y-%m-%d')}.")
                        st.rerun()
                except Exception as e: st.error(f"❌ Failed to reset Oasis allocations: {e}"); conn_reset_oa.rollback()
                finally: return_connection(pool, conn_reset_oa)
        
        if st.button("🧽 Remove All Oasis Preferences (Global Action)", key="btn_reset_all_oasis_prefs_confirmable"):
            st.session_state.confirm_op_reset = True
        
        if st.session_state.get("confirm_op_reset"):
            st.warning("⚠️ Are you sure you want to remove ALL Oasis preferences? This cannot be undone.")
            col1_op, col2_op = st.columns(2)
            with col1_op:
                if st.button("YES, DELETE ALL OASIS PREFERENCES", key="btn_confirm_delete_op_yes"):
                    conn_reset_op = get_connection(pool)
                    if conn_reset_op:
                        try:
                            with conn_reset_op.cursor() as cur:
                                cur.execute("DELETE FROM oasis_preferences")
                                conn_reset_op.commit()
                                st.success("✅ All Oasis preferences removed.")
                                st.session_state.confirm_op_reset = False
                                st.rerun()
                        except Exception as e: st.error(f"❌ Failed: {e}"); conn_reset_op.rollback()
                        finally: return_connection(pool, conn_reset_op)
            with col2_op:
                if st.button("NO, CANCEL OASIS PREFERENCES DELETION", key="btn_confirm_delete_op_no"):
                    st.session_state.confirm_op_reset = False
                    st.rerun()

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
                                team_size_val = int(row["Size"]) if pd.notnull(row["Size"]) else 3 
                                cur.execute("INSERT INTO weekly_preferences (team_name, contact_person, team_size, preferred_days, submission_time) VALUES (%s, %s, %s, %s, %s)",
                                            (row["Team"], row["Contact"], team_size_val, row["Days"], sub_time) )
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
    For teams of 3 or more. Submissions for the **week of {st.session_state.get("submission_week_of_text", default_submission_week_of_text)}** are open
    from **{st.session_state.get("submission_start_text", "Wednesday 4 June 09:00")}** until **{st.session_state.get("submission_end_text", "Thursday 5 June 16:00")}**.
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
    Submit your personal preferences for the **week of {st.session_state.get("submission_week_of_text", default_submission_week_of_text)}**.
    Submissions open from **{st.session_state.get("submission_start_text", "Wednesday 4 June 09:00")}** until **{st.session_state.get("oasis_end_text", "Friday 6 June 16:00")}**.
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
st.markdown(st.session_state.get('project_allocations_display_markdown_content', default_project_alloc_markdown))
alloc_display_df = get_room_grid(pool, st.session_state.project_rooms_display_monday)
if alloc_display_df.empty:
    st.write(f"No project room allocations yet for the week of {st.session_state.project_rooms_display_monday.strftime('%d %B %Y')}.")
else:
    st.dataframe(alloc_display_df, use_container_width=True, hide_index=True)

# -----------------------------------------------------
# Ad-hoc Oasis Addition
# -----------------------------------------------------
st.header("🚶 Add Yourself to Oasis (Ad-hoc)")
current_oasis_display_mon_adhoc = st.session_state.oasis_display_monday
st.caption(f"Use this if you missed preference submission. Subject to availability for week of {current_oasis_display_mon_adhoc.strftime('%d %B %Y')}.")
with st.form("oasis_add_form_main"):
    adhoc_oasis_name = st.text_input("Your Name", key="af_adhoc_name")
    adhoc_oasis_days = st.multiselect(
        f"Select day(s) for week starting {current_oasis_display_mon_adhoc.strftime('%d %B')}:",
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
                        
                        for day_str in adhoc_oasis_days:
                            date_obj_check = current_oasis_display_mon_adhoc + timedelta(days=days_map_indices[day_str])
                            cur.execute("DELETE FROM weekly_allocations WHERE room_name = 'Oasis' AND team_name = %s AND date = %s", (name_clean, date_obj_check))
                        
                        added_to_all_selected = True
                        actually_added_days = []
                        for day_str in adhoc_oasis_days:
                            date_obj = current_oasis_display_mon_adhoc + timedelta(days=days_map_indices[day_str])
                            cur.execute("SELECT COUNT(*) FROM weekly_allocations WHERE room_name = 'Oasis' AND date = %s", (date_obj,))
                            count_result = cur.fetchone()
                            count = count_result[0] if count_result else 0

                            if count >= oasis.get("capacity", 15):
                                st.warning(f"⚠️ Oasis is full on {day_str} ({date_obj.strftime('%d %B')}). Could not add {name_clean}.")
                                added_to_all_selected = False
                            else:
                                cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, 'Oasis', %s)", (name_clean, date_obj))
                                actually_added_days.append(day_str)
                        conn_adhoc.commit()
                        if actually_added_days:
                             st.success(f"✅ {name_clean} processed for Oasis for {', '.join(actually_added_days)} in week of {current_oasis_display_mon_adhoc.strftime('%d %B')}!")
                        if not added_to_all_selected and adhoc_oasis_days :
                             st.info("ℹ️ Check messages above for details on your ad-hoc Oasis additions. Some days might have been full.")
                        elif not actually_added_days and adhoc_oasis_days:
                             st.error("❌ Could not add to Oasis for any selected day (likely full).")

                        st.rerun()
                except Exception as e:
                    st.error(f"❌ Error adding to Oasis: {e}")
                    if conn_adhoc: conn_adhoc.rollback()
                finally: return_connection(pool, conn_adhoc)

# -----------------------------------------------------
# Full Weekly Oasis Overview
# -----------------------------------------------------
st.header("📊 Full Weekly Oasis Overview")
st.markdown(st.session_state.get('oasis_allocations_display_markdown_content', default_oasis_alloc_markdown))
oasis_overview_monday_display = st.session_state.oasis_display_monday
oasis_overview_days_dates = [oasis_overview_monday_display + timedelta(days=i) for i in range(5)]
oasis_overview_day_names = [d.strftime("%A") for d in oasis_overview_days_dates]
oasis_capacity = oasis.get("capacity", 15)

conn_matrix = get_connection(pool)
if not conn_matrix: st.error("No DB connection for Oasis Overview")
else:
    try:
        with conn_matrix.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute( 
                "SELECT team_name, date FROM weekly_allocations WHERE room_name = 'Oasis' AND date >= %s AND date <= %s",
                (oasis_overview_monday_display, oasis_overview_days_dates[-1])
            )
            rows = cur.fetchall()

        df_matrix_data = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["team_name", "date"])
        if not df_matrix_data.empty:
            df_matrix_data["date"] = pd.to_datetime(df_matrix_data["date"]).dt.date

        unique_names_allocated = set(df_matrix_data["team_name"]) if not df_matrix_data.empty else set()
        names_from_prefs = set()
        try: 
            with conn_matrix.cursor(cursor_factory=RealDictCursor) as cur: 
                cur.execute("SELECT DISTINCT person_name FROM oasis_preferences")
                pref_rows = cur.fetchall()
                names_from_prefs = {row["person_name"] for row in pref_rows}
        except psycopg2.Error: st.warning("Could not fetch names from Oasis preferences for matrix display.")
        
        all_relevant_names_list = list(unique_names_allocated.union(names_from_prefs))
        if "Niek" not in all_relevant_names_list:
             all_relevant_names_list.append("Niek")
        all_relevant_names = sorted(list(set(all_relevant_names_list)))
        
        if not all_relevant_names:
            initial_matrix_df = pd.DataFrame(columns=oasis_overview_day_names)
        else:
            initial_matrix_df = pd.DataFrame(False, index=all_relevant_names, columns=oasis_overview_day_names)

            if not df_matrix_data.empty: 
                for _, row_data in df_matrix_data.iterrows():
                    person_name = row_data["team_name"]
                    alloc_date = row_data["date"]
                    if alloc_date in oasis_overview_days_dates and person_name in initial_matrix_df.index:
                        initial_matrix_df.at[person_name, alloc_date.strftime("%A")] = True
            
            if "Niek" in initial_matrix_df.index: 
                for day_n in oasis_overview_day_names: initial_matrix_df.at["Niek", day_n] = True
        
        st.subheader("🪑 Oasis Availability Summary")
        current_day_alloc_counts = {day_dt: 0 for day_dt in oasis_overview_days_dates}
        if not df_matrix_data.empty:
            for day_dt_check in oasis_overview_days_dates:
                current_day_alloc_counts[day_dt_check] = df_matrix_data[df_matrix_data["date"] == day_dt_check]["team_name"].nunique()

        for day_dt, day_str_label in zip(oasis_overview_days_dates, oasis_overview_day_names):
            used_spots = current_day_alloc_counts[day_dt]
            spots_left = max(0, oasis_capacity - used_spots)
            st.markdown(f"**{day_str_label}**: {spots_left} spot(s) left (out of {oasis_capacity})")

        if not initial_matrix_df.empty:
            edited_matrix = st.data_editor(
                initial_matrix_df, 
                use_container_width=True,
                disabled=["Niek"] if "Niek" in initial_matrix_df.index else [], 
                key="oasis_matrix_editor_main"
            )

            if st.button("💾 Save Oasis Matrix Changes", key="btn_save_oasis_matrix_changes"):
                try:
                    with conn_matrix.cursor() as cur:
                        cur.execute("DELETE FROM weekly_allocations WHERE room_name = 'Oasis' AND team_name != 'Niek' AND date >= %s AND date <= %s", (oasis_overview_monday_display, oasis_overview_days_dates[-1]))
                        
                        if "Niek" in edited_matrix.index: 
                            cur.execute("DELETE FROM weekly_allocations WHERE room_name = 'Oasis' AND team_name = 'Niek' AND date >= %s AND date <= %s", (oasis_overview_monday_display, oasis_overview_days_dates[-1]))
                            for day_idx, day_col_name in enumerate(oasis_overview_day_names):
                                if edited_matrix.at["Niek", day_col_name]:
                                    cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)", ("Niek", "Oasis", oasis_overview_monday_display + timedelta(days=day_idx)))
                        
                        occupied_counts_per_day = {day_col: 0 for day_col in oasis_overview_day_names}
                        if "Niek" in edited_matrix.index: 
                            for day_col_name in oasis_overview_day_names:
                                if edited_matrix.at["Niek", day_col_name]:
                                    occupied_counts_per_day[day_col_name] +=1
                                    
                        for person_name_matrix in edited_matrix.index: 
                            if person_name_matrix == "Niek": continue 
                            for day_idx, day_col_name in enumerate(oasis_overview_day_names):
                                if edited_matrix.at[person_name_matrix, day_col_name]: 
                                    if occupied_counts_per_day[day_col_name] < oasis_capacity:
                                        alloc_date = oasis_overview_monday_display + timedelta(days=day_idx)
                                        cur.execute("INSERT INTO weekly_allocations (team_name, room_name, date) VALUES (%s, %s, %s)", (person_name_matrix, "Oasis", alloc_date))
                                        occupied_counts_per_day[day_col_name] += 1
                                    else:
                                        alloc_date_str = (oasis_overview_monday_display + timedelta(days=day_idx)).strftime('%d %b')
                                        st.warning(f"⚠️ {person_name_matrix} could not be added to Oasis on {day_col_name} ({alloc_date_str}): capacity ({oasis_capacity}) reached.")
                                        
                        conn_matrix.commit()
                        st.success("✅ Oasis Matrix saved successfully!")
                        st.rerun()
                except Exception as e_matrix_save:
                    st.error(f"❌ Failed to save Oasis Matrix: {e_matrix_save}")
                    if conn_matrix: conn_matrix.rollback()
        else:
            st.info(f"No Oasis data to display or edit for the week of {oasis_overview_monday_display.strftime('%d %B %Y')}.")

    except Exception as e_matrix_load:
        st.error(f"❌ Error loading Oasis Matrix data: {e_matrix_load}")
    finally: return_connection(pool, conn_matrix)

# -----------------------------------------------------
# Final Note: DB connectivity check
# -----------------------------------------------------
if not pool:
    st.error("🚨 Cannot connect to the database. Please check configurations or contact an admin. Some parts of the application may not function correctly.")
