import streamlit as st
import time
from client import ApiClient
from shared.ui import sidebar_api_key

st.set_page_config(
    page_title="Scholar Survey",
    page_icon="🎓",
    layout="centered"
)

# Initialize API Client and Sidebar
if 'api_client' not in st.session_state:
    st.session_state.api_client = ApiClient()

api_key = sidebar_api_key()

st.title("🎓 Google Scholar Survey")
st.markdown("Automated systematic literature review and data extraction.")

# Server Health Check
if not st.session_state.api_client.get_health():
    st.error("⚠️ Cannot connect to backend server. Is it running? (Run `python start_system.py`)")
    st.stop()

# --- Job Submission ---
st.header("Start New Search")

with st.form("search_form"):
    query = st.text_input("Search Query", placeholder='e.g., "generative ai" AND "software engineering"')
    
    col1, col2 = st.columns(2)
    with col1:
        since_year = st.number_input("Since Year", min_value=1900, max_value=2025, value=2020)
        max_results = st.number_input("Max Results", min_value=10, max_value=1000, value=100)
    
    with col2:
        # Get sites from shared/constant if possible, or hardcode common ones
        DEFAULT_SITES = [
            "sciencedirect.com", "ieeexplore.ieee.org", "link.springer.com", 
            "dl.acm.org", "onlinelibrary.wiley.com", "arxiv.org"
        ]
        sites = st.multiselect("Restrict to Sites", options=DEFAULT_SITES)
        download_pdfs = st.checkbox("Download PDFs", value=False)
        
    submitted = st.form_submit_button("Submit Job")

if submitted:
    if query:
        try:
            with st.spinner("Submitting job..."):
                job_id = st.session_state.api_client.submit_job(
                    query=query,
                    max_results=max_results,
                    since_year=since_year,
                    sites=sites,
                    download_pdfs=download_pdfs
                )
            
            st.success(f"Job submitted successfully! ID: `{job_id}`")
            st.info("Navigate to 'Job Monitor' in the sidebar to track progress.")
            
        except Exception as e:
            st.error(f"Failed to submit job: {e}")
    else:
        st.warning("Please enter a search query.")

st.divider()

st.markdown("""
### Quick Links
- 📊 **[Job Monitor](/job_monitor)**: Check status and results
- 🧙‍♂️ **[SLR Wizard](/slr_wizard)**: AI-assisted review workflow
""")
