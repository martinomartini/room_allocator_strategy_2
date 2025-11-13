"""
Credential Browser - Search and View Database

Browse and search the credentials database without generating presentations.
"""

import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="Credential Browser",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Credential Browser")
st.markdown("Search and browse the credentials database")

@st.cache_data
def load_credentials_data():
    """Load credentials database"""
    excel_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'credentials_full.xlsx')
    try:
        df = pd.read_excel(excel_path)
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def find_person_projects(df: pd.DataFrame, person_name: str) -> pd.DataFrame:
    """Find all projects for a specific person"""
    partner_col = None
    manager_col = None
    
    for col in df.columns:
        col_lower = col.lower()
        if 'partner' in col_lower and 'engagement' in col_lower:
            partner_col = col
        elif 'manager' in col_lower and 'engagement' in col_lower:
            manager_col = col
    
    mask = pd.Series([False] * len(df))
    
    if partner_col:
        mask |= df[partner_col].astype(str).str.lower().str.contains(
            person_name.lower(), na=False
        )
    
    if manager_col:
        mask |= df[manager_col].astype(str).str.lower().str.contains(
            person_name.lower(), na=False
        )
    
    return df[mask].copy()

# Load data
df = load_credentials_data()

if df is not None and not df.empty:
    
    # Get available people
    partners = []
    managers = []
    
    for col in df.columns:
        col_lower = col.lower()
        if 'partner' in col_lower and 'engagement' in col_lower:
            partners = sorted([str(x) for x in df[col].dropna().unique()])
        elif 'manager' in col_lower and 'engagement' in col_lower:
            managers = sorted([str(x) for x in df[col].dropna().unique()])
    
    all_people = sorted(set(partners + managers))
    
    st.sidebar.header("🔍 Search Options")
    
    # Person selection
    search_mode = st.sidebar.radio(
        "Search by:",
        ["Select Person", "Search All Projects"]
    )
    
    if search_mode == "Select Person":
        selected_person = st.sidebar.selectbox(
            "Select a person:",
            [""] + all_people,
            index=0
        )
        
        if selected_person:
            # Find projects
            person_projects = find_person_projects(df, selected_person)
            
            st.success(f"✅ Found **{len(person_projects)} projects** for **{selected_person}**")
            
            # Additional filters
            st.sidebar.markdown("---")
            st.sidebar.subheader("📊 Filters")
            
            # Year filter
            if "Year of completion" in person_projects.columns:
                years = sorted(person_projects["Year of completion"].dropna().unique(), reverse=True)
                selected_years = st.sidebar.multiselect(
                    "Filter by Year:",
                    years,
                    default=years
                )
                if selected_years:
                    person_projects = person_projects[person_projects["Year of completion"].isin(selected_years)]
            
            # Industry filter
            if "Industry" in person_projects.columns:
                industries = sorted(person_projects["Industry"].dropna().unique())
                selected_industries = st.sidebar.multiselect(
                    "Filter by Industry:",
                    industries
                )
                if selected_industries:
                    person_projects = person_projects[person_projects["Industry"].isin(selected_industries)]
            
            # Sector filter
            if "Sector" in person_projects.columns:
                sectors = sorted(person_projects["Sector"].dropna().unique())
                selected_sectors = st.sidebar.multiselect(
                    "Filter by Sector:",
                    sectors
                )
                if selected_sectors:
                    person_projects = person_projects[person_projects["Sector"].isin(selected_sectors)]
            
            st.info(f"Showing **{len(person_projects)} projects** after filters")
            
            # Display projects
            if len(person_projects) > 0:
                # Select columns to display
                display_columns = [
                    "Project name / engagement title",
                    "Client name",
                    "Year of completion",
                    "Industry",
                    "Sector",
                    "Service offering / proposition",
                    "Engagement partner",
                    "Engagement manager",
                    "Credential description including proposition (tombstone appropriate)"
                ]
                
                # Only show columns that exist
                display_columns = [col for col in display_columns if col in person_projects.columns]
                
                # Display dataframe
                st.dataframe(
                    person_projects[display_columns],
                    width="stretch",
                    height=400
                )
                
                # Export options
                st.markdown("---")
                st.subheader("📥 Export Options")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Export to CSV
                    csv = person_projects[display_columns].to_csv(index=False)
                    st.download_button(
                        label="📄 Download as CSV",
                        data=csv,
                        file_name=f"credentials_{selected_person.replace(' ', '_')}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    # Export to Excel
                    from io import BytesIO
                    excel_buffer = BytesIO()
                    person_projects[display_columns].to_excel(excel_buffer, index=False, engine='openpyxl')
                    excel_buffer.seek(0)
                    
                    st.download_button(
                        label="📊 Download as Excel",
                        data=excel_buffer.getvalue(),
                        file_name=f"credentials_{selected_person.replace(' ', '_')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.warning("No projects match the selected filters.")
        else:
            st.info("👈 Please select a person from the sidebar to view their projects.")
    
    else:  # Search All Projects
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Filters")
        
        # Client search
        client_search = st.sidebar.text_input("Search Client Name:")
        
        # Year filter
        if "Year of completion" in df.columns:
            years = sorted(df["Year of completion"].dropna().unique(), reverse=True)
            selected_years = st.sidebar.multiselect(
                "Filter by Year:",
                years
            )
        
        # Industry filter
        if "Industry" in df.columns:
            industries = sorted(df["Industry"].dropna().unique())
            selected_industries = st.sidebar.multiselect(
                "Filter by Industry:",
                industries
            )
        
        # Sector filter
        if "Sector" in df.columns:
            sectors = sorted(df["Sector"].dropna().unique())
            selected_sectors = st.sidebar.multiselect(
                "Filter by Sector:",
                sectors
            )
        
        # Apply filters
        filtered_df = df.copy()
        
        if client_search:
            filtered_df = filtered_df[
                filtered_df["Client name"].astype(str).str.lower().str.contains(client_search.lower(), na=False)
            ]
        
        if selected_years:
            filtered_df = filtered_df[filtered_df["Year of completion"].isin(selected_years)]
        
        if selected_industries:
            filtered_df = filtered_df[filtered_df["Industry"].isin(selected_industries)]
        
        if selected_sectors:
            filtered_df = filtered_df[filtered_df["Sector"].isin(selected_sectors)]
        
        st.success(f"✅ Found **{len(filtered_df)} projects** matching filters (from {len(df)} total)")
        
        # Display projects
        if len(filtered_df) > 0:
            display_columns = [
                "Project name / engagement title",
                "Client name",
                "Year of completion",
                "Industry",
                "Sector",
                "Service offering / proposition",
                "Engagement partner",
                "Engagement manager"
            ]
            
            display_columns = [col for col in display_columns if col in filtered_df.columns]
            
            st.dataframe(
                filtered_df[display_columns],
                width="stretch",
                height=400
            )
            
            # Export
            st.markdown("---")
            csv = filtered_df[display_columns].to_csv(index=False)
            st.download_button(
                label="📄 Download Results as CSV",
                data=csv,
                file_name="filtered_credentials.csv",
                mime="text/csv"
            )
        else:
            st.warning("No projects match the selected filters.")

else:
    st.error("❌ Failed to load credentials database")
    st.info("Please ensure 'credentials_full.xlsx' exists in the root folder")
