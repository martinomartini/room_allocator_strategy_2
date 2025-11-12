import streamlit as st
import pandas as pd
import os

# Page configuration
st.set_page_config(
    page_title="Project Database Viewer",
    page_icon="📊",
    layout="wide"
)

# Password protection
PASSWORD = "bud123"

# Initialize session state for authentication
if "authenticated_project_db" not in st.session_state:
    st.session_state.authenticated_project_db = False

# Authentication check
if not st.session_state.authenticated_project_db:
    st.title("🔐 Project Database - Access Required")
    st.info("Please enter the password to access the Project Database Viewer.")
    
    password_input = st.text_input("Enter password:", type="password", key="db_password")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔓 Login", use_container_width=True):
            if password_input == PASSWORD:
                st.session_state.authenticated_project_db = True
                st.success("✅ Access granted! Redirecting...")
                st.rerun()
            else:
                st.error("❌ Incorrect password. Please try again.")
    
    st.stop()

# Once authenticated, show the content
st.title("📊 Project Database Viewer")

# Add logout button
col1, col2, col3 = st.columns([6, 1, 1])
with col3:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated_project_db = False
        st.rerun()

# Load the Excel file
@st.cache_data
def load_data():
    """Load data from Excel file in credentials folder"""
    # Look for the Excel file in the credentials folder
    credentials_folder = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        '..',
        'credentials'
    )
    excel_path = os.path.join(credentials_folder, 'test_data_credentials.xlsx')
    
    try:
        df = pd.read_excel(excel_path)
        return df, None
    except FileNotFoundError:
        return None, f"File not found: {excel_path}"
    except Exception as e:
        return None, f"Error loading Excel file: {e}"

# Load the data
df, error = load_data()

if df is not None:
    st.success(f"✅ Data loaded successfully! Total projects: {len(df)}")
    
    # Create tabs for different filter options
    tab1, tab2, tab3 = st.tabs(["🏭 Filter by Industry", "👤 Filter by Partner", "👔 Filter by Manager"])
    
    with tab1:
        st.subheader("Filter by Industry")
        
        # Get unique industries (handle potential column name variations)
        industry_col = None
        secondary_industry_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if 'industry' in col_lower and 'secondary' not in col_lower:
                industry_col = col
            elif 'secondary' in col_lower and 'industry' in col_lower:
                secondary_industry_col = col
        
        if industry_col:
            # Create dropdown for primary industry
            industries = ['All'] + sorted([str(x) for x in df[industry_col].dropna().unique()])
            selected_industry = st.selectbox("Select Primary Industry", industries, key='industry')
            
            # Filter by primary industry
            if selected_industry != 'All':
                filtered_df = df[df[industry_col] == selected_industry]
            else:
                filtered_df = df.copy()
            
            # If secondary industry column exists, add filter
            if secondary_industry_col:
                secondary_industries = ['All'] + sorted([str(x) for x in df[secondary_industry_col].dropna().unique()])
                selected_secondary = st.selectbox("Select Secondary Industry", secondary_industries, key='secondary')
                
                if selected_secondary != 'All':
                    filtered_df = filtered_df[filtered_df[secondary_industry_col] == selected_secondary]
            
            # Display results
            st.write(f"**Showing {len(filtered_df)} project(s)**")
            if len(filtered_df) > 0:
                st.dataframe(filtered_df, use_container_width=True, height=500)
            else:
                st.info("No projects found for the selected filters.")
        else:
            st.warning("No industry column found in the Excel file.")
    
    with tab2:
        st.subheader("Filter by Engagement Partner")
        
        # Find engagement partner column
        partner_col = None
        for col in df.columns:
            col_lower = col.lower()
            if 'partner' in col_lower and 'engagement' in col_lower:
                partner_col = col
                break
            elif 'partner' in col_lower:
                partner_col = col
        
        if partner_col:
            partners = ['All'] + sorted([str(x) for x in df[partner_col].dropna().unique()])
            selected_partner = st.selectbox("Select Engagement Partner", partners, key='partner')
            
            if selected_partner != 'All':
                filtered_df = df[df[partner_col] == selected_partner]
            else:
                filtered_df = df.copy()
            
            # Display results
            st.write(f"**Showing {len(filtered_df)} project(s)**")
            if len(filtered_df) > 0:
                st.dataframe(filtered_df, use_container_width=True, height=500)
            else:
                st.info("No projects found for the selected partner.")
        else:
            st.warning("No engagement partner column found in the Excel file.")
    
    with tab3:
        st.subheader("Filter by Engagement Manager")
        
        # Find engagement manager column
        manager_col = None
        for col in df.columns:
            col_lower = col.lower()
            if 'manager' in col_lower and 'engagement' in col_lower:
                manager_col = col
                break
            elif 'manager' in col_lower:
                manager_col = col
        
        if manager_col:
            managers = ['All'] + sorted([str(x) for x in df[manager_col].dropna().unique()])
            selected_manager = st.selectbox("Select Engagement Manager", managers, key='manager')
            
            if selected_manager != 'All':
                filtered_df = df[df[manager_col] == selected_manager]
            else:
                filtered_df = df.copy()
            
            # Display results
            st.write(f"**Showing {len(filtered_df)} project(s)**")
            if len(filtered_df) > 0:
                st.dataframe(filtered_df, use_container_width=True, height=500)
            else:
                st.info("No projects found for the selected manager.")
        else:
            st.warning("No engagement manager column found in the Excel file.")
    
    # Add a section to show column information
    with st.expander("ℹ️ Data Information"):
        st.write("**Available Columns:**")
        st.write(list(df.columns))
        st.write(f"\n**Total Records:** {len(df)}")
        st.write(f"**Total Columns:** {len(df.columns)}")

elif error:
    st.error(f"❌ {error}")
    st.info("💡 Please check:")
    st.info("1. The file 'test_data_credentials.xlsx' exists in the credentials folder")
    st.info("2. The file is not open in another program")
    st.info("3. You have read permissions for the file")
else:
    st.error("Failed to load data. Please check if the Excel file exists in the credentials folder.")

# Add navigation tip
st.markdown("---")
st.info("💡 **Tip**: Use the sidebar to navigate back to the main Room Allocator app or other pages.")
