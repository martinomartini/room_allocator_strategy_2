"""
Credentials Management System - Download

Download the standalone application with all three AI-powered tools.
"""

import streamlit as st
import os

st.set_page_config(
    page_title="Credentials System - Download",
    page_icon="📥",
    layout="wide"
)

st.title("📥 Credentials Management System")
st.markdown("Download the complete standalone application with AI-powered tools")
st.markdown("---")

# Create columns for centered download button
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # GitHub download button
    github_repo = "martinomartini/room_allocator_strategy_2"
    download_url = f"https://github.com/{github_repo}/archive/refs/heads/main.zip"
    
    st.link_button(
        "⬇️ Download Credentials System",
        download_url,
        type="primary",
        use_container_width=True
    )
    
    st.markdown("""
    **Quick Start:**
    1. Extract ZIP file
    2. Open `standalone/` folder
    3. Double-click `Launch.bat`
    4. Password: **bud123**
    """)

st.markdown("---")

# Show what's included
col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown("### � Project Database")
    st.markdown("AI chat for querying projects")

with col_b:
    st.markdown("### � Credential Browser")
    st.markdown("Fast search and filtering")

with col_c:
    st.markdown("### 📝 PowerPoint Generator")
    st.markdown("AI-powered presentations")

st.caption("Requires KPMG network access for AI features")
