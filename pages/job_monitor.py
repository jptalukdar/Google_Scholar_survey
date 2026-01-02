import streamlit as st
import pandas as pd
import time
from client import ApiClient
from shared.ui import sidebar_api_key

st.set_page_config(page_title="Job Monitor", page_icon="📊", layout="wide")
api_key = sidebar_api_key()

st.title("📊 Job Monitor")

if 'api_client' not in st.session_state:
    st.session_state.api_client = ApiClient()

client = st.session_state.api_client

# Refresh button
if st.button("🔄 Refresh"):
    st.rerun()

# List jobs
try:
    jobs = client.list_jobs()
except Exception as e:
    st.error(f"Failed to fetch jobs: {e}")
    st.stop()

if not jobs:
    st.info("No jobs found.")
else:
    # Convert to DataFrame for display
    df = pd.DataFrame(jobs)
    
    # Display table
    st.dataframe(
        df[["id", "query", "status", "progress", "total_results", "created_at"]],
        use_container_width=True,
        hide_index=True
    )
    
    st.divider()
    
    # Job Details
    st.subheader("Job Details")
    selected_job_id = st.selectbox("Select Job", options=[j['id'] for j in jobs], format_func=lambda x: f"{x} - {next((j['query'] for j in jobs if j['id'] == x), '')}")
    
    if selected_job_id:
        job_detail = client.get_job(selected_job_id)
        
        if job_detail:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Status", job_detail['status'])
                pg = job_detail['progress']
                st.progress(pg if pg <= 1.0 else 1.0)
            with col2:
                st.metric("Results Found", job_detail['total_results'])
            with col3:
                # Cancel button
                if job_detail['status'] in ["pending", "running"]:
                    if st.button("🛑 Cancel Job"):
                        if client.cancel_job(selected_job_id):
                            st.success("Cancellation requested.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to cancel.")

            # Tabs for Logs and Results
            tab1, tab2 = st.tabs(["📝 Logs", "📄 Results"])
            
            with tab1:
                logs = job_detail.get('logs', [])
                if logs:
                    st.code("\n".join(logs[-20:])) # Show last 20 lines
                    with st.expander("Full Logs"):
                        st.code("\n".join(logs))
                else:
                    st.info("No logs available.")
            
            with tab2:
                results = job_detail.get('results', [])
                if results:
                    st.dataframe(pd.DataFrame(results))
                    
                    # Download CSV
                    csv = pd.DataFrame(results).to_csv(index=False)
                    st.download_button(
                        "📥 Download Results CSV",
                        csv,
                        "results.csv",
                        "text/csv"
                    )
                else:
                    st.info("No results yet.")
