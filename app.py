import streamlit as st
import psycopg2
import psycopg2.pool # Import the pool module
import json
import os
from datetime import datetime
import pytz
import pandas as pd # For displaying data

# --- Configuration ---

# Attempt to load secrets from Streamlit secrets management first, then environment variables
# These MUST be set either in Streamlit Cloud secrets or as environment variables where deployed
DATABASE_URL = st.secrets.get("SUPABASE_DB_URI", os.environ.get("SUPABASE_DB_URI"))
OFFICE_TIMEZONE_STR = st.secrets.get("OFFICE_TIMEZONE", os.environ.get("OFFICE_TIMEZONE", "UTC")) # Default to UTC if not set

try:
    OFFICE_TIMEZONE = pytz.timezone(OFFICE_TIMEZONE_STR)
except pytz.exceptions.UnknownTimeZoneError:
    st.error(f"Invalid Timezone configured: '{OFFICE_TIMEZONE_STR}'. Please set a valid timezone (e.g., 'Europe/London', 'America/New_York') in secrets. Defaulting to UTC.")
    OFFICE_TIMEZONE = pytz.utc # Fallback to UTC

# Load room data from JSON file relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOMS_FILE = os.path.join(BASE_DIR, 'rooms.json')

try:
    with open(ROOMS_FILE, 'r') as f:
        AVAILABLE_ROOMS = json.load(f)
except FileNotFoundError:
    st.error(f"CRITICAL ERROR: Room configuration file '{ROOMS_FILE}' not found. The application cannot function without it.")
    AVAILABLE_ROOMS = []
    st.stop() # Stop execution if rooms file is missing
except json.JSONDecodeError:
    st.error(f"CRITICAL ERROR: Could not decode '{ROOMS_FILE}'. Check if it's valid JSON. Application cannot function.")
    AVAILABLE_ROOMS = []
    st.stop() # Stop execution if JSON is invalid

# --- Database Helper Functions ---

# Use st.cache_resource to manage the database connection pool efficiently
# This prevents reconnecting on every script rerun within a session.
@st.cache_resource
def get_db_connection_pool():
    """Creates a connection pool for the database."""
    if not DATABASE_URL:
        st.error("Database connection string (SUPABASE_DB_URI) is not configured. Please set it in Streamlit secrets.")
        return None # Return None if URL is missing
    try:
        # Using minconn=1, maxconn=5 as an example pool size. Adjust as needed.
        pool = psycopg2.pool.SimpleConnectionPool(minconn=1, maxconn=5, dsn=DATABASE_URL)
        return pool
    except Exception as e:
        st.error(f"Database connection pool error: {e}. Check connection string and database status.")
        return None # Return None on error

def get_connection_from_pool(_pool):
    """Gets a connection from the pool."""
    if _pool:
        try:
            return _pool.getconn()
        except Exception as e:
            st.error(f"Failed to get connection from pool: {e}")
            return None
    st.error("Connection pool is not available.")
    return None

def return_connection_to_pool(_pool, conn):
    """Returns a connection to the pool."""
    if _pool and conn:
        try:
            _pool.putconn(conn)
        except Exception as e:
            st.warning(f"Failed to return connection to pool: {e}") # Warn but don't crash

def get_current_reservations_df(_pool):
    """Gets current reservations as a Pandas DataFrame."""
    reservations = []
    conn = get_connection_from_pool(_pool)
    if not conn:
        st.warning("Could not connect to database to fetch current reservations.")
        return pd.DataFrame(reservations) # Return empty DataFrame

    try:
        with conn.cursor() as cur:
            # Select relevant columns and format timestamp nicely in the specified office timezone
            cur.execute("""
                SELECT team_name, contact_person, team_size, assigned_room_name,
                       to_char(reservation_time AT TIME ZONE %s, 'YYYY-MM-DD HH24:MI') as reservation_time_local
                FROM reservations
                ORDER BY assigned_room_name ASC
            """, (OFFICE_TIMEZONE_STR,)) # Pass timezone string for DB conversion
            results = cur.fetchall()
            # Get column names from cursor description for robust mapping
            colnames = [desc[0] for desc in cur.description]
            reservations = [dict(zip(colnames, row)) for row in results]
    except psycopg2.Error as db_err:
        st.warning(f"Database error fetching reservations: {db_err}")
    except Exception as e:
        st.warning(f"Unexpected error fetching reservations: {e}")
    finally:
        return_connection_to_pool(_pool, conn) # Ensure connection is returned

    # Convert list of dicts to DataFrame with user-friendly column names
    if reservations:
        df = pd.DataFrame(reservations)
        df.columns = ["Team Name", "Contact", "Size", "Assigned Room", "Reserved At (Local)"]
        return df
    else:
        return pd.DataFrame() # Return empty DataFrame if no reservations


# --- Streamlit App UI and Logic ---

st.set_page_config(page_title="Office Room Allocator", layout="centered")
st.title("🏢 Office Room Allocator")

# Check database connection URL is present before proceeding
if not DATABASE_URL:
    st.error("Application setup incomplete: Database connection string (SUPABASE_DB_URI) is missing.")
    st.stop()

# Attempt to get the database pool
db_pool = get_db_connection_pool()
if not db_pool:
     st.error("Application halted: Failed to establish database connection pool. Please check configuration and database status.")
     st.stop()


# Display Time Information and Reservation Status
now_local = datetime.now(OFFICE_TIMEZONE)
current_hour = now_local.hour
is_reservation_time = (0 <= current_hour < 9) # Check if current hour is between 0 (midnight) and 8 (up to 8:59)

st.info(f"""
Current Office Time ({OFFICE_TIMEZONE_STR}): **{now_local.strftime('%Y-%m-%d %H:%M:%S')}**
Reservations are currently **{'🟢 OPEN' if is_reservation_time else '🔴 CLOSED'}**.
(Booking window: 00:00 - 09:00 daily in office time)
""")

# Reservation Form Section
st.header("Make a Reservation")

# Disable form elements if outside reservation time
form_disabled = not is_reservation_time

# Use a form to group inputs and submit button
with st.form("reservation_form", clear_on_submit=True):
    team_name = st.text_input("Your Team Name:", key="team_name_input", placeholder="e.g., Project Phoenix", disabled=form_disabled)
    contact_person = st.text_input("Contact Person:", key="contact_person_input", placeholder="e.g., Jane Doe", disabled=form_disabled)
    team_size = st.number_input("Team Size (Number of People):", min_value=1, step=1, key="team_size_input", help="Enter the total number of people needing a seat.", disabled=form_disabled)

    # Submit button within the form
    submitted = st.form_submit_button("Find and Reserve Room", disabled=form_disabled)

    if submitted:
        # --- Form Submission Logic ---
        # Re-check time constraint *at the moment of submission* as a safeguard
        now_local_submit = datetime.now(OFFICE_TIMEZONE)
        if not (0 <= now_local_submit.hour < 9):
            st.error("Sorry, the reservation window closed just now (00:00-09:00). Please try again tomorrow.")
        # Validate inputs
        elif not team_name or not contact_person or team_size <= 0:
            st.warning("⚠️ Please fill in all fields with valid information.")
        else:
            # Proceed with reservation logic inside a spinner
            with st.spinner("Checking availability and attempting reservation..."):
                conn_submit = get_connection_from_pool(db_pool)
                if not conn_submit:
                     st.error("Database connection failed during submission attempt. Please try again.")
                else:
                    assigned_room = None # Initialize assigned_room
                    try:
                        # Get currently reserved rooms *within this transaction* for consistency
                        reserved_room_names = set()
                        with conn_submit.cursor() as cur:
                            # Lock the table briefly if high concurrency is expected (optional, depends on DB load)
                            # cur.execute("LOCK TABLE reservations IN SHARE ROW EXCLUSIVE MODE;")
                            cur.execute("SELECT DISTINCT assigned_room_name FROM reservations")
                            results = cur.fetchall()
                            for row in results:
                                reserved_room_names.add(row[0])

                        # Find Suitable Room logic
                        # Filter rooms by capacity and availability, then sort by capacity (smallest first)
                        suitable_rooms = sorted(
                            [room for room in AVAILABLE_ROOMS if room['capacity'] >= team_size and room['name'] not in reserved_room_names],
                            key=lambda x: x['capacity']
                        )

                        if not suitable_rooms:
                            st.error(f"😔 Sorry, no available room found right now that can fit a team of {team_size}. Try again later if others cancel, or check tomorrow.")
                            # No commit/rollback needed here as nothing was inserted yet
                        else:
                            assigned_room = suitable_rooms[0] # Assign the smallest suitable room

                            # Attempt to Add Reservation within the same transaction
                            try:
                                with conn_submit.cursor() as cur:
                                    cur.execute(
                                        "INSERT INTO reservations (team_name, contact_person, team_size, assigned_room_name) VALUES (%s, %s, %s, %s)",
                                        (team_name, contact_person, team_size, assigned_room['name'])
                                    )
                                conn_submit.commit() # Commit the transaction if insert is successful
                                st.success(f"✅ Success! Team '{team_name}' has been assigned to room '{assigned_room['name']}'.")
                            except psycopg2.Error as insert_db_err:
                                st.error(f"Database error saving reservation: {insert_db_err}")
                                try:
                                    conn_submit.rollback() # Roll back if insert fails
                                except Exception as rb_e:
                                     st.warning(f"Rollback failed: {rb_e}")
                            except Exception as insert_e:
                                st.error(f"Unexpected error saving reservation: {insert_e}")
                                try:
                                    conn_submit.rollback()
                                except Exception as rb_e:
                                     st.warning(f"Rollback failed: {rb_e}")

                    except psycopg2.Error as fetch_db_err:
                        st.error(f"Database error checking reservations: {fetch_db_err}")
                        # No rollback needed if fetch fails before insert attempt
                    except Exception as fetch_e:
                        st.error(f"Unexpected error checking reservations: {fetch_e}")
                    finally:
                        return_connection_to_pool(db_pool, conn_submit) # Always return connection


# Display Current Reservations Section (outside the form)
st.divider() # Visual separator
st.header("Current Reservations for Today")
st.caption(f"Showing reservations for {now_local.strftime('%Y-%m-%d')}. This list automatically updates.")

with st.spinner("Loading current reservations..."):
    reservations_df = get_current_reservations_df(db_pool)

if reservations_df.empty:
    st.write("No rooms reserved yet for today.")
else:
    # Use st.dataframe for a nice interactive table display
    st.dataframe(reservations_df, hide_index=True, use_container_width=True)

# --- Footer or additional info ---
st.divider()
st.caption("This system resets daily at 18:00 UTC. Reservations are for the current day only.")

# --- End of App ---
