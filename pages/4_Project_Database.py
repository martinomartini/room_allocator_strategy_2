import streamlit as st
import pandas as pd
import os
import requests
import json
from typing import Dict, List, Optional
from io import BytesIO
from datetime import datetime
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ==== Workbench API Configuration ====
API_URL = "https://api.workbench.kpmg/genai/azure/inference/chat/completions?api-version=2024-12-01-preview"

# Default values (always pre-filled)
DEFAULT_SUBSCRIPTION_KEY = "b82fef87872349b981d5c0d58afb55c1"
DEFAULT_CHARGE_CODE = "1"
DEFAULT_DEPLOYMENT = "gpt-4o-2024-08-06-dzs-we"

def get_api_config():
    """Get API configuration from secrets, environment variables, session state, or defaults"""
    # Initialize session state for API config if not exists
    if "api_config" not in st.session_state:
        # Try to get from Streamlit secrets first, then environment variables, then use defaults
        try:
            secrets = st.secrets.get("workbench", {})
            subscription_key = (
                secrets.get("subscription_key") or 
                os.environ.get("WORKBENCH_SUBSCRIPTION_KEY") or 
                DEFAULT_SUBSCRIPTION_KEY
            )
            charge_code = (
                secrets.get("charge_code") or 
                os.environ.get("WORKBENCH_CHARGE_CODE") or 
                DEFAULT_CHARGE_CODE
            )
            deployment = (
                secrets.get("deployment") or 
                os.environ.get("WORKBENCH_DEPLOYMENT") or 
                DEFAULT_DEPLOYMENT
            )
        except:
            # No secrets file, use environment variables or defaults
            subscription_key = os.environ.get("WORKBENCH_SUBSCRIPTION_KEY") or DEFAULT_SUBSCRIPTION_KEY
            charge_code = os.environ.get("WORKBENCH_CHARGE_CODE") or DEFAULT_CHARGE_CODE
            deployment = os.environ.get("WORKBENCH_DEPLOYMENT") or DEFAULT_DEPLOYMENT
        
        st.session_state.api_config = {
            "subscription_key": subscription_key,
            "charge_code": charge_code,
            "deployment": deployment
        }
    
    return st.session_state.api_config

def get_api_headers():
    """Get API headers with current configuration"""
    config = get_api_config()
    return {
        'Ocp-Apim-Subscription-Key': config["subscription_key"],
        'Cache-Control': 'no-cache',
        'x-kpmg-charge-code': config["charge_code"],
        'azureml-model-deployment': config["deployment"]
    }

# Page configuration
st.set_page_config(
    page_title="Project Database Viewer with Chat",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)




# Password protection
PASSWORD = "bud123"

# Initialize session state for authentication
if "authenticated_project_db" not in st.session_state:
    st.session_state.authenticated_project_db = False

# Authentication check
if not st.session_state.authenticated_project_db:
    st.title("🔐 Project Database - Access Required")
    st.info("Please enter the password to access the Project Database Viewer with AI Chat.")
    
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


# Title
st.title("📊 Project Database Viewer with AI Chat")


# Add logout button
col1, col2, col3 = st.columns([6, 1, 1])
with col3:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.authenticated_project_db = False
        st.rerun()



@st.cache_data
def load_data_from_excel():
    """Load data from Excel file"""
    excel_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'credentials_full.xlsx'
    )
    try:
        df = pd.read_excel(excel_path)
        return df
    except FileNotFoundError:
        return None
    except Exception as e:
        return None

def get_column_mapping(df: pd.DataFrame) -> Dict[str, str]:
    """Create a mapping of common terms to actual column names"""
    if df is None or df.empty:
        return {}
    mapping = {}
    for col in df.columns:
        col_lower = col.lower()
        if 'industry' in col_lower and 'secondary' not in col_lower:
            mapping['industry'] = col
            mapping['primary_industry'] = col
        elif 'secondary' in col_lower and 'industry' in col_lower:
            mapping['secondary_industry'] = col
        elif 'partner' in col_lower and 'engagement' in col_lower:
            mapping['partner'] = col
            mapping['engagement_partner'] = col
        elif 'manager' in col_lower and 'engagement' in col_lower:
            mapping['manager'] = col
            mapping['engagement_manager'] = col
        elif 'project' in col_lower or 'engagement' in col_lower:
            mapping['project_name'] = col
        elif 'client' in col_lower and 'name' in col_lower and 'confidential' not in col_lower:
            mapping['client'] = col
            mapping['client_name'] = col
        elif 'year' in col_lower and 'completion' in col_lower:
            mapping['year'] = col
            mapping['year_of_completion'] = col
        elif 'sector' in col_lower:
            mapping['sector'] = col
        elif 'service' in col_lower and 'offering' in col_lower:
            mapping['service'] = col
            mapping['service_offering'] = col
    return mapping


def export_to_excel(df: pd.DataFrame, filename: str = None) -> BytesIO:
    """Export DataFrame to Excel format"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"projects_export_{timestamp}.xlsx"
    
    excel_buffer = BytesIO()
    try:
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name="Projects", index=False)
        excel_buffer.seek(0)
        return excel_buffer
    except Exception as e:
        st.error(f"Error exporting to Excel: {str(e)}")
        return None

def call_workbench_api(user_query: str, context: str, df: pd.DataFrame, conversation_history: List[Dict] = None) -> Optional[str]:
    """Call the workbench API to interpret the user query"""
    # Get API config (always has default values)
    config = get_api_config()
    subscription_key = config.get("subscription_key", "").strip()
    
    # If no key provided (empty or just whitespace), return None
    if not subscription_key:
        return None
    
    # Get sample values for key columns to help the API understand the data
    industry_col = None
    partner_col = None
    manager_col = None
    year_col = None
    client_col = None
    
    for col in df.columns:
        col_lower = col.lower()
        if 'industry' in col_lower and 'secondary' not in col_lower:
            industry_col = col
        elif 'partner' in col_lower and 'engagement' in col_lower:
            partner_col = col
        elif 'manager' in col_lower and 'engagement' in col_lower:
            manager_col = col
        elif 'year' in col_lower and 'completion' in col_lower:
            year_col = col
        elif 'client' in col_lower and 'name' in col_lower and 'confidential' not in col_lower:
            client_col = col
    
    # Get ALL sample values to help with better matching (especially for names)
    sample_industries = sorted([str(x) for x in df[industry_col].dropna().unique()][:20]) if industry_col else []
    sample_partners = sorted([str(x) for x in df[partner_col].dropna().unique()]) if partner_col else []  # Get ALL partners
    sample_managers = sorted([str(x) for x in df[manager_col].dropna().unique()]) if manager_col else []  # Get ALL managers
    sample_clients = sorted([str(x) for x in df[client_col].dropna().unique()][:20]) if client_col else []
    sample_years = sorted([str(x) for x in df[year_col].dropna().unique()]) if year_col else []
    
    # Build a comprehensive list of all partners and managers for name matching
    all_partners_managers = sample_partners + sample_managers
    partners_managers_list = ', '.join(all_partners_managers[:50]) if len(all_partners_managers) > 50 else ', '.join(all_partners_managers)
    
    system_prompt = f"""You are a helpful assistant that interprets natural language queries about project data and extracts filter criteria.

Available columns in the dataset: {', '.join(list(df.columns)[:20])}

**ALL AVAILABLE PARTNERS AND MANAGERS (for name matching):**
{partners_managers_list if partners_managers_list else 'None found'}

Sample values to help with matching:
- Industries: {', '.join(sample_industries[:15]) if sample_industries else 'N/A'}
- Partners: {len(sample_partners)} total partners available (see full list above)
- Managers: {len(sample_managers)} total managers available (see full list above)
- Years: {', '.join(sample_years) if sample_years else 'N/A'}
- Sample Clients: {', '.join(sample_clients[:10]) if sample_clients else 'N/A'}

CRITICAL RULE FOR NAME MATCHING:
When a user mentions a PERSON'S NAME (like "Tim Kramer", "John Doe", "Charbel Moussa"):
1. FIRST: Check if the name appears in the PARTNERS list above (case-insensitive, partial matching allowed)
2. SECOND: If not in partners, check if it appears in the MANAGERS list above
3. ONLY if the name is NOT found in partners OR managers, then check clients
4. For queries like "projects of [Name]" or "projects by [Name]", ALWAYS prioritize partner/manager over client

Name matching rules:
- Use case-insensitive partial matching (e.g., "Tim Kramer" matches "Tim Kramer", "tim kramer", "Kramer", etc.)
- If a name appears in the partners/managers list above, use that filter (partner or manager)
- ONLY use "client" filter for company/organization names, NOT person names
- Person names should ALWAYS be matched against partners/managers first

The user will ask questions about projects. Your job is to extract filter criteria from their query and return ONLY a JSON object with the following structure:
{{
    "filters": {{
        "industry": "exact or partial value to match (use null if not applicable)",
        "secondary_industry": "exact or partial value to match (use null if not applicable)",
        "partner": "exact or partial partner name to match (MUST CHECK PARTNERS LIST FIRST for person names - use null if not applicable)",
        "manager": "exact or partial manager name to match (CHECK MANAGERS LIST if not in partners - use null if not applicable)",
        "year": "year as string like '2024' or '2025' (use null if not applicable)",
        "sector": "exact or partial value to match (use null if not applicable)",
        "client": "exact or partial client/company name (ONLY use if name is NOT in partners/managers lists - use null if not applicable)",
        "project_name": "exact or partial project name (use null if not applicable)",
        "service": "exact or partial service offering (use null if not applicable)"
    }},
    "search_text": "any text to search across all columns or null",
    "explanation": "brief explanation of what you understood"
}}

IMPORTANT RULES:
1. NAME MATCHING PRIORITY: For person names → Check partners list FIRST, then managers list, ONLY THEN clients.
2. When matching names, use case-insensitive partial matching against the partners/managers lists provided above.
3. If the query asks for something vague like "all projects in industry" without specifying WHICH industry, set that filter to null.
4. Only extract specific, concrete values.
5. For queries like "give me all projects of Tim Kramer" → Check if "Tim Kramer" is in the partners/managers list. If yes, use partner or manager filter. If no, then check clients.

Example queries:
- "Show me all projects in the paper industry" -> {{"filters": {{"industry": "paper"}}, "search_text": null, "explanation": "Filtering by paper industry"}}
- "Give me all projects of Tim Kramer" -> First check if "Tim Kramer" is in partners list. If found: {{"filters": {{"partner": "Tim Kramer"}}, "search_text": null, "explanation": "Filtering by partner Tim Kramer"}}. If in managers: {{"filters": {{"manager": "Tim Kramer"}}, ...}}. ONLY if not in either, check clients.
- "Projects by Charbel Moussa" -> Check partners/managers lists first. If found: {{"filters": {{"partner": "Charbel Moussa"}}, ...}}
- "All projects from 2025" -> {{"filters": {{"year": "2025"}}, "search_text": null, "explanation": "Filtering by year 2025"}}
- "Projects for Microsoft" (clearly a company) -> {{"filters": {{"client": "Microsoft"}}, "search_text": null, "explanation": "Filtering by client Microsoft"}}

Return ONLY valid JSON, no other text."""

    try:
        # Build messages with conversation history for context
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if available (for context continuity)
        if conversation_history and len(conversation_history) > 1:
            # Include recent conversation history (last 8 messages for context, excluding the current query)
            # This helps maintain conversation flow and allows follow-up questions
            recent_history = conversation_history[:-1]  # Exclude the last message (current query)
            # Limit to last 6 messages to avoid token limits
            if len(recent_history) > 6:
                recent_history = recent_history[-6:]
            
            for msg in recent_history:
                if msg.get("role") in ["user", "assistant"]:
                    # Clean up the content (remove dataframe references if any)
                    content = msg.get("content", "")
                    # Only include text content, not dataframes
                    if content and not isinstance(content, pd.DataFrame):
                        # Limit content length to prevent token overflow
                        clean_content = str(content)[:300]
                        messages.append({"role": msg["role"], "content": clean_content})
        
        # Add current user query with full context
        query_with_context = f"Dataset context: {context}\n\nCurrent user query: {user_query}"
        messages.append({"role": "user", "content": query_with_context})
        
        body = {
            "messages": messages,
            "max_completion_tokens": 500,
            "temperature": 0.3
        }
        
        headers = get_api_headers()
        response = requests.post(
            API_URL,
            headers=headers,
            json=body,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        elif response.status_code == 401:
            # Invalid API key
            return None
        elif response.status_code == 403:
            # Access forbidden - likely IP allowlisting issue
            return None
        else:
            # Return None for any other error to trigger the friendly message
            return None
            
    except Exception as e:
        st.error(f"Error calling API: {str(e)}")
        return None

def parse_api_response(response_text: str) -> Optional[Dict]:
    """Parse the API response and extract filter criteria"""
    try:
        # Try to extract JSON from the response (it might have markdown formatting)
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        result = json.loads(response_text)
        return result
    except json.JSONDecodeError as e:
        st.error(f"Error parsing API response: {str(e)}")
        st.text(f"Response was: {response_text}")
        return None

def has_meaningful_filters(filter_criteria: Dict, column_mapping: Dict[str, str]) -> bool:
    """Check if filter criteria contains any meaningful filters"""
    filters = filter_criteria.get('filters', {})
    search_text = filter_criteria.get('search_text')
    
    # Check if any filter has a non-null, non-empty value
    for key, value in filters.items():
        if value and value != "null" and str(value).strip() and key in column_mapping:
            return True
    
    # Check if search text is meaningful
    if search_text and search_text != "null" and str(search_text).strip():
        return True
    
    return False

def apply_filters(df: pd.DataFrame, filter_criteria: Dict, column_mapping: Dict[str, str]) -> pd.DataFrame:
    """Apply filters to the dataframe based on the criteria"""
    filtered_df = df.copy()
    
    filters = filter_criteria.get('filters', {})
    filters_applied = 0
    
    for key, value in filters.items():
        if value and value != "null" and str(value).strip() and key in column_mapping:
            col_name = column_mapping[key]
            if col_name in filtered_df.columns:
                # Handle case-insensitive partial matching
                before_count = len(filtered_df)
                filtered_df = filtered_df[
                    filtered_df[col_name].astype(str).str.lower().str.contains(
                        str(value).lower(), na=False
                    )
                ]
                if len(filtered_df) != before_count:
                    filters_applied += 1
    
    # Apply text search if provided
    search_text = filter_criteria.get('search_text')
    if search_text and search_text != "null" and str(search_text).strip():
        before_count = len(filtered_df)
        mask = pd.Series([False] * len(filtered_df))
        for col in filtered_df.columns:
            mask |= filtered_df[col].astype(str).str.lower().str.contains(
                search_text.lower(), na=False
            )
        filtered_df = filtered_df[mask]
        if len(filtered_df) != before_count:
            filters_applied += 1
    
    return filtered_df

# Sidebar is hidden - Configuration uses defaults automatically
# Initialize API config with defaults (no UI, just backend)
if "api_config" not in st.session_state:
    config = get_api_config()
    st.session_state.api_config = config

# Add refresh button in main area (optional - you can remove this if not needed)
# Or keep it hidden in sidebar but functional

# Load data from Excel file
df = load_data_from_excel()

# Main content area
if df is not None and not df.empty:
    # Data source info and refresh button are hidden - data loads automatically
    # Store original dataframe before any filtering
    original_df = df.copy()
    
    # Get column mapping
    column_mapping = get_column_mapping(original_df)
    
    # Get key columns for statistics
    industry_col = column_mapping.get('industry')
    partner_col = column_mapping.get('partner')
    manager_col = column_mapping.get('manager')
    sector_col = column_mapping.get('sector')
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬 Chat Query", 
        "📊 Statistics",
        "🏭 Filter by Industry", 
        "👤 Filter by Partner", 
        "👔 Filter by Manager"
    ])
    
    with tab1:
        st.subheader("💬 AI Chat Feature")
        st.info("🤖 **AI-Powered Search:** Ask questions in natural language! API credentials are pre-configured. If you get an error, use the other tabs which always work.")
        st.caption("Examples: 'Show me all projects in technology', 'Give me all projects of Tim Kramer', 'All projects from 2024'")
        
        # Initialize chat history
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
        
        # Initialize conversation context for API
        if "conversation_context" not in st.session_state:
            st.session_state.conversation_context = []
        
        # Display chat history
        for idx, message in enumerate(st.session_state.chat_messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "filtered_results" in message and message["filtered_results"] is not None:
                    results_df = message["filtered_results"]
                    st.dataframe(results_df, use_container_width=True)
                    st.caption(f"Found {len(results_df)} project(s)")
        
        # Chat input
        if prompt := st.chat_input("Ask about projects..."):
            # Add user message to history
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            # Add to conversation context for API
            st.session_state.conversation_context.append({"role": "user", "content": prompt})
            st.rerun()
        
        # Process the last message if it's a user message without a response
        # Check if the last message needs a response
        needs_response = False
        if st.session_state.chat_messages:
            last_msg = st.session_state.chat_messages[-1]
            # Need response if last message is from user
            if last_msg["role"] == "user":
                # Check if there's already a response
                # If it's the first message, or if the previous message was from assistant (meaning this is a new user question)
                if len(st.session_state.chat_messages) == 1:
                    # First message from user - always needs response
                    needs_response = True
                elif len(st.session_state.chat_messages) > 1:
                    # Check if previous message was from assistant (meaning we need to respond to new user message)
                    if st.session_state.chat_messages[-2]["role"] == "assistant":
                        needs_response = True
                    # If previous was also user, that means we're still processing (shouldn't happen, but handle it)
                    elif st.session_state.chat_messages[-2]["role"] == "user":
                        needs_response = True
        
        if needs_response:
            user_prompt = st.session_state.chat_messages[-1]["content"]
            
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                message_placeholder.markdown("🤔 Thinking...")
                
                # Get API config and check if we have a valid key
                config = get_api_config()
                subscription_key = config.get("subscription_key", "").strip()
                
                if not subscription_key:
                    error_msg = """ℹ️ **AI Chat Unavailable**

The AI chat requires KPMG Workbench API access which is not configured.

**✅ All Other Features Work Great:**
- Navigate to the **Statistics** tab for overview
- Use **Industry**, **Partner**, or **Manager** tabs to filter projects
- Export data to CSV or Excel
- Select which columns to display

Click on the other tabs above to explore the database!"""
                    message_placeholder.info(error_msg)
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "filtered_results": None
                    })
                    # Add to conversation context
                    st.session_state.conversation_context.append({"role": "assistant", "content": error_msg})
                else:
                    # Call API to interpret query with conversation context
                    context = f"Dataset has {len(original_df)} projects. Key columns include: Industry, Secondary industry, Engagement partner, Engagement manager, Year of completion, Sector, Client name, Project name, Service offering."
                    
                    # Build conversation context for API (include all messages except current)
                    # Pass the full conversation context so API can understand follow-up questions
                    conversation_messages = st.session_state.conversation_context
                    
                    api_response = call_workbench_api(user_prompt, context, original_df, conversation_messages)
                    
                    if api_response:
                        filter_criteria = parse_api_response(api_response)
                        
                        if filter_criteria:
                            explanation = filter_criteria.get('explanation', 'Processing your query...')
                            
                            # Check if meaningful filters were provided
                            if not has_meaningful_filters(filter_criteria, column_mapping):
                                # Get sample values for the clarification message
                                sample_industries = sorted([str(x) for x in original_df[industry_col].dropna().unique()][:8]) if industry_col and industry_col in original_df.columns else []
                                sample_partners = sorted([str(x) for x in original_df[partner_col].dropna().unique()][:8]) if partner_col and partner_col in original_df.columns else []
                                sample_managers = sorted([str(x) for x in original_df[manager_col].dropna().unique()][:8]) if manager_col and manager_col in original_df.columns else []
                                year_col = column_mapping.get('year')
                                sample_years = sorted([str(x) for x in original_df[year_col].dropna().unique()]) if year_col and year_col in original_df.columns else []
                                sample_sectors = sorted([str(x) for x in original_df[sector_col].dropna().unique()][:8]) if sector_col and sector_col in original_df.columns else []
                                
                                clarification_msg = f"""⚠️ **Query needs clarification**

Your query "{user_prompt}" is too vague. Please be more specific.

**Examples of good queries:**
- "Show me all projects in the **paper industry**"
- "Give me all projects of **Tim Kramer**" (searches partners/managers)
- "Find projects by **Charbel Moussa**"
- "Show me projects from **2025**"
- "Projects in the **technology** sector"

**Available options in the data:**

{f'• **Industries**: {", ".join(sample_industries)}' + ('...' if len(sample_industries) >= 10 else '') if sample_industries else ''}
{f'• **Partners**: {", ".join(sample_partners)}' + ('...' if len(sample_partners) >= 10 else '') if sample_partners else ''}
{f'• **Managers**: {", ".join(sample_managers)}' + ('...' if len(sample_managers) >= 10 else '') if sample_managers else ''}
{f'• **Years**: {", ".join(sample_years)}' if sample_years else ''}
{f'• **Sectors**: {", ".join(sample_sectors)}' + ('...' if len(sample_sectors) >= 10 else '') if sample_sectors else ''}

Please try again with a more specific query, or use the filter tabs below!"""
                                
                                message_placeholder.warning(clarification_msg)
                                clarification_response = {
                                    "role": "assistant",
                                    "content": clarification_msg,
                                    "filtered_results": None
                                }
                                st.session_state.chat_messages.append(clarification_response)
                                # Add to conversation context
                                st.session_state.conversation_context.append({
                                    "role": "assistant",
                                    "content": clarification_msg
                                })
                            else:
                                message_placeholder.markdown(f"💡 {explanation}")
                                
                                # Apply filters to original dataframe
                                filtered_df = apply_filters(original_df, filter_criteria, column_mapping)
                                
                                if len(filtered_df) > 0:
                                    st.dataframe(filtered_df, use_container_width=True)
                                    st.caption(f"✅ Found {len(filtered_df)} project(s)")
                                    
                                    # Add to chat history
                                    assistant_response = {
                                        "role": "assistant",
                                        "content": explanation,
                                        "filtered_results": filtered_df
                                    }
                                    st.session_state.chat_messages.append(assistant_response)
                                    # Add to conversation context (without the dataframe)
                                    st.session_state.conversation_context.append({
                                        "role": "assistant",
                                        "content": explanation
                                    })
                                else:
                                    st.info("ℹ️ No projects found matching your criteria. Try adjusting your search terms.")
                                    assistant_response = {
                                        "role": "assistant",
                                        "content": explanation + "\n\nNo projects found matching your criteria.",
                                        "filtered_results": None
                                    }
                                    st.session_state.chat_messages.append(assistant_response)
                                    # Add to conversation context
                                    st.session_state.conversation_context.append({
                                        "role": "assistant",
                                        "content": explanation + "\n\nNo projects found matching your criteria."
                                    })
                        else:
                            error_response = "Sorry, I couldn't understand your query. Please try rephrasing or use the filter tabs below."
                            message_placeholder.error("❌ Could not parse the query. Please try rephrasing your question.")
                            st.session_state.chat_messages.append({
                                "role": "assistant",
                                "content": error_response,
                                "filtered_results": None
                            })
                            # Add to conversation context
                            st.session_state.conversation_context.append({
                                "role": "assistant",
                                "content": error_response
                            })
                    else:
                        error_msg = """ℹ️ **AI Chat Not Available**

The KPMG Workbench API cannot be reached from this environment (403 error).

**✅ Good News - Everything Else Works:**
- **Statistics** tab - View charts and metrics
- **Industry** tab - Filter by sector
- **Partner** tab - Browse by partner
- **Manager** tab - Search by manager
- Export and column selection features

**Switch to another tab to continue exploring!**"""
                        message_placeholder.info(error_msg)
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "content": error_msg,
                            "filtered_results": None
                        })
                        # Add to conversation context
                        st.session_state.conversation_context.append({
                            "role": "assistant",
                            "content": error_msg
                        })
        
        # Clear chat button
        if st.button("🗑️ Clear Chat History", key="clear_chat"):
            st.session_state.chat_messages = []
            st.session_state.conversation_context = []
            st.rerun()
    
    # Helper function to display filtered results with export and column selection
    def display_filtered_results(filtered_df: pd.DataFrame, tab_name: str, industry_col=None, partner_col=None):
        """Display filtered results with export functionality and column selection"""
        if filtered_df is None or filtered_df.empty:
            st.info("No projects found for the selected filters.")
            return
        
        # UPGRADE 1 & 2: Export and Column Selection
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"**Showing {len(filtered_df)} project(s)**")
        
        with col2:
            # UPGRADE 1: Export to CSV
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="📥 Export CSV",
                data=csv,
                file_name=f"projects_{tab_name}_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True,
                key=f"export_csv_{tab_name}"
            )
        
        with col3:
            # UPGRADE 1: Export to Excel
            try:
                excel_buffer = export_to_excel(filtered_df, f"projects_{tab_name}_{timestamp}.xlsx")
                if excel_buffer:
                    st.download_button(
                        label="📥 Export Excel",
                        data=excel_buffer.getvalue(),
                        file_name=f"projects_{tab_name}_{timestamp}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key=f"export_excel_{tab_name}"
                    )
            except Exception as e:
                st.error(f"Excel export error: {str(e)}")
        
        # UPGRADE 2: Column Selection
        with st.expander("⚙️ Select Columns to Display", expanded=False):
            all_columns = list(filtered_df.columns)
            if f"selected_columns_{tab_name}" not in st.session_state:
                # Default to first 10 columns or all if less than 10
                st.session_state[f"selected_columns_{tab_name}"] = all_columns[:min(10, len(all_columns))]
            
            selected_columns = st.multiselect(
                "Choose columns to display",
                all_columns,
                default=st.session_state.get(f"selected_columns_{tab_name}", all_columns[:min(10, len(all_columns))]),
                key=f"column_selector_{tab_name}"
            )
            
            # Update session state - if empty, show all columns
            if selected_columns:
                st.session_state[f"selected_columns_{tab_name}"] = selected_columns
            else:
                st.session_state[f"selected_columns_{tab_name}"] = all_columns
        
        # Display dataframe with selected columns
        columns_to_display = st.session_state.get(f"selected_columns_{tab_name}", list(filtered_df.columns))
        display_df = filtered_df[columns_to_display] if columns_to_display else filtered_df
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=500
        )
        
        # Show statistics for filtered data
        with st.expander("📊 Filtered Data Statistics"):
            stat_col1, stat_col2 = st.columns(2)
            
            with stat_col1:
                if industry_col and industry_col in filtered_df.columns:
                    st.write("**Projects by Industry (Filtered):**")
                    industry_counts = filtered_df[industry_col].value_counts()
                    st.dataframe(industry_counts, use_container_width=True)
            
            with stat_col2:
                if partner_col and partner_col in filtered_df.columns:
                    st.write("**Projects by Partner (Filtered):**")
                    partner_counts = filtered_df[partner_col].value_counts()
                    st.dataframe(partner_counts, use_container_width=True)
    
    # Statistics Tab (tab2)
    with tab2:
        st.subheader("📊 Summary Statistics")
        st.caption("Overview of project data statistics and visualizations")
        
        # Create metrics columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Projects", len(original_df))
        
        with col2:
            if industry_col and industry_col in original_df.columns:
                st.metric("Unique Industries", original_df[industry_col].nunique())
            else:
                st.metric("Unique Industries", "N/A")
        
        with col3:
            if partner_col and partner_col in original_df.columns:
                st.metric("Unique Partners", original_df[partner_col].nunique())
            else:
                st.metric("Unique Partners", "N/A")
        
        with col4:
            if manager_col and manager_col in original_df.columns:
                st.metric("Unique Managers", original_df[manager_col].nunique())
            else:
                st.metric("Unique Managers", "N/A")
        
        st.markdown("---")
        
        # Visualizations
        viz_col1, viz_col2 = st.columns(2)
        
        with viz_col1:
            if industry_col and industry_col in original_df.columns:
                st.write("**Top 10 Industries**")
                industry_counts = original_df[industry_col].value_counts().head(10)
                if PLOTLY_AVAILABLE:
                    fig = px.bar(
                        x=industry_counts.values,
                        y=industry_counts.index,
                        orientation='h',
                        labels={'x': 'Count', 'y': 'Industry'},
                        title="Projects by Industry"
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.bar_chart(industry_counts)
            else:
                st.info("Industry data not available")
        
        with viz_col2:
            if partner_col and partner_col in original_df.columns:
                st.write("**Top 10 Partners**")
                partner_counts = original_df[partner_col].value_counts().head(10)
                if PLOTLY_AVAILABLE:
                    fig = px.bar(
                        x=partner_counts.values,
                        y=partner_counts.index,
                        orientation='h',
                        labels={'x': 'Count', 'y': 'Partner'},
                        title="Projects by Partner"
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.bar_chart(partner_counts)
            else:
                st.info("Partner data not available")
        
        # Additional statistics
        st.markdown("---")
        st.subheader("📈 Additional Statistics")
        
        stat_col1, stat_col2 = st.columns(2)
        
        with stat_col1:
            if manager_col and manager_col in original_df.columns:
                st.write("**Top 10 Managers**")
                manager_counts = original_df[manager_col].value_counts().head(10)
                if PLOTLY_AVAILABLE:
                    fig = px.bar(
                        x=manager_counts.values,
                        y=manager_counts.index,
                        orientation='h',
                        labels={'x': 'Count', 'y': 'Manager'},
                        title="Projects by Manager"
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.bar_chart(manager_counts)
            else:
                st.info("Manager data not available")
        
        with stat_col2:
            if sector_col and sector_col in original_df.columns:
                st.write("**Top 10 Sectors**")
                sector_counts = original_df[sector_col].value_counts().head(10)
                if PLOTLY_AVAILABLE:
                    fig = px.bar(
                        x=sector_counts.values,
                        y=sector_counts.index,
                        orientation='h',
                        labels={'x': 'Count', 'y': 'Sector'},
                        title="Projects by Sector"
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.bar_chart(sector_counts)
            else:
                st.info("Sector data not available")
    
    # Filter by Industry Tab (tab3)
    with tab3:
        st.subheader("🏭 Filter by Industry")
        
        # Get unique industries
        filter_industry_col = None
        secondary_industry_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if 'industry' in col_lower and 'secondary' not in col_lower:
                filter_industry_col = col
            elif 'secondary' in col_lower and 'industry' in col_lower:
                secondary_industry_col = col
        
        if filter_industry_col:
            # Create dropdown for primary industry
            industries = ['All'] + sorted([str(x) for x in original_df[filter_industry_col].dropna().unique()])
            selected_industry = st.selectbox("Select Primary Industry", industries, key='industry')
            
            # Filter by primary industry
            if selected_industry != 'All':
                filtered_df = original_df[original_df[filter_industry_col] == selected_industry].copy()
            else:
                filtered_df = original_df.copy()
            
            # If secondary industry column exists, add filter
            if secondary_industry_col:
                secondary_industries = ['All'] + sorted([str(x) for x in original_df[secondary_industry_col].dropna().unique()])
                selected_secondary = st.selectbox("Select Secondary Industry", secondary_industries, key='secondary')
                
                if selected_secondary != 'All':
                    filtered_df = filtered_df[filtered_df[secondary_industry_col] == selected_secondary]
            
            # Display results with export and column selection
            display_filtered_results(filtered_df, "industry", industry_col=industry_col, partner_col=partner_col)
        else:
            st.warning("No industry column found in the Excel file.")
    
    # Filter by Partner Tab (tab4)
    with tab4:
        st.subheader("👤 Filter by Engagement Partner")
        
        # Find engagement partner column (use the one from column mapping)
        filter_partner_col = partner_col
        if not filter_partner_col:
            # Fallback: search for it
            for col in df.columns:
                col_lower = col.lower()
                if 'partner' in col_lower and 'engagement' in col_lower:
                    filter_partner_col = col
                    break
                elif 'partner' in col_lower:
                    filter_partner_col = col
        
        if filter_partner_col:
            partners = ['All'] + sorted([str(x) for x in original_df[filter_partner_col].dropna().unique()])
            selected_partner = st.selectbox("Select Engagement Partner", partners, key='partner')
            
            if selected_partner != 'All':
                # Convert both sides to string for comparison to handle any data type issues
                filtered_df = original_df[original_df[filter_partner_col].astype(str) == str(selected_partner)].copy()
            else:
                filtered_df = original_df.copy()
            
            # Display results with export and column selection
            display_filtered_results(filtered_df, "partner", industry_col=industry_col, partner_col=filter_partner_col)
        else:
            st.warning(f"No engagement partner column found in the Excel file. Available columns: {list(df.columns)}")
    
    # Filter by Manager Tab (tab5)
    with tab5:
        st.subheader("👔 Filter by Engagement Manager")
        
        # Find engagement manager column (use the one from column mapping)
        filter_manager_col = manager_col
        if not filter_manager_col:
            # Fallback: search for it
            for col in df.columns:
                col_lower = col.lower()
                if 'manager' in col_lower and 'engagement' in col_lower:
                    filter_manager_col = col
                    break
                elif 'manager' in col_lower:
                    filter_manager_col = col
        
        if filter_manager_col:
            managers = ['All'] + sorted([str(x) for x in original_df[filter_manager_col].dropna().unique()])
            selected_manager = st.selectbox("Select Engagement Manager", managers, key='manager')
            
            if selected_manager != 'All':
                # Convert both sides to string for comparison to handle any data type issues
                filtered_df = original_df[original_df[filter_manager_col].astype(str) == str(selected_manager)].copy()
            else:
                filtered_df = original_df.copy()
            
            # Display results with export and column selection
            display_filtered_results(filtered_df, "manager", industry_col=industry_col, partner_col=partner_col)
        else:
            st.warning(f"No engagement manager column found in the Excel file. Available columns: {list(df.columns)}")
    
    # Add a section to show column information
    with st.expander("ℹ️ Data Information"):
        st.write("**Available Columns:**")
        st.write(list(original_df.columns))
        st.write(f"\n**Total Records:** {len(original_df)}")
        st.write(f"**Total Columns:** {len(original_df.columns)}")

else:
    # Failed to load data from Excel
    st.error("❌ Failed to load data from Excel file.")
    st.info("💡 Please check:")
    st.info("1. The file 'credentials_full.xlsx' exists in the credentials folder")
    st.info("2. The file is not open in another program")
    st.info("3. You have read permissions for the file")
    st.info(f"💡 Expected file path: {os.path.join(os.path.dirname(__file__), 'credentials_full.xlsx')}")

