"""
Credentials Management System - Download

Download the standalone application with all three AI-powered tools.
"""

import streamlit as st

st.set_page_config(
    page_title="Credentials System - Download",
    page_icon="📥",
    layout="wide"
)

st.title("📥 Credentials Management System")
st.markdown("One-click installer with all AI-powered tools")
st.markdown("---")

# Create columns for centered download button
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # GitHub download button
    github_repo = "martinomartini/room_allocator_strategy_2"
    download_url = f"https://github.com/{github_repo}/archive/refs/heads/main.zip"
    
    st.markdown("### 🚀 One-Click Download")
    st.link_button(
        "⬇️ Download Credentials System",
        download_url,
        type="primary",
        use_container_width=True
    )
    
    st.info("""
    **What you get:**
    - ✅ Self-installing application
    - ✅ All 3 AI-powered tools
    - ✅ Automatic dependency installation
    - ✅ No manual setup required!
    """)
    
    st.markdown("""
    **Installation Steps:**
    1. Extract ZIP file
    2. Open `room_allocator_strategy_2-main/standalone/` folder
    3. Double-click `Launch.bat`
    4. Wait for automatic setup (first time only)
    5. Enter password: **bud123**
    
    **Requirements:**
    - Windows PC
    - Python 3.8+ ([Download here](https://www.python.org/downloads/) if needed)
    - KPMG network access for AI features
    
    💡 The launcher will automatically install all dependencies on first run!
    """)

st.markdown("---")

# Show what's included
st.markdown("### 📦 Included Tools")
col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown("#### 📊 Project Database")
    st.markdown("""
    - AI chat for natural language queries
    - Filter by industry, partner, year
    - Export to CSV/Excel
    - Password protected
    """)

with col_b:
    st.markdown("#### 🔍 Credential Browser")
    st.markdown("""
    - Fast search and filtering
    - Search by person name
    - Filter by multiple criteria
    - Quick export options
    """)

with col_c:
    st.markdown("#### 📝 PowerPoint Generator")
    st.markdown("""
    - AI-powered presentations
    - Natural language requests
    - Smart project selection
    - Professional output
    """)

st.markdown("---")
st.caption("⚠️ AI features require KPMG network access (VPN or on-premises) • Password for all tools: bud123")
