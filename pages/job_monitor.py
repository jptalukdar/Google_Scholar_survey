import streamlit as st
import pandas as pd
import time
from api import JobManager
from workers.job import JobStatus

st.set_page_config(page_title="Job Monitor", layout="wide")
st.title("Job Monitor")

manager = JobManager()

# Sidebar - Refresh
refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 1, 60, 5)

if st.sidebar.button("Refresh Now"):
    st.rerun()

# List Jobs
st.subheader("Active Jobs")
jobs = manager.list_jobs()

if not jobs:
    st.info("No jobs found.")
else:
    # Create a nice dataframe view
    job_data = []
    for job in jobs:
        try:
             job_data.append({
                "Job ID": job.id,
                "Query": job.query,
                "Status": job.status.value,
                "Progress": f"{job.progress*100:.1f}%",
                "Results": job.total_results,
                "Created At": job.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })
        except:
             continue # Handle malformed jobs gracefully

    df = pd.DataFrame(job_data)
    
    # Custom styling for status? Streamlit data editor is good enough
    event = st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        selection_mode="single-row",
        on_select="rerun"
    )

    # Job Details Selection
    selected_rows = event.selection.rows
    if selected_rows:
        selected_index = selected_rows[0]
        selected_job_id = df.iloc[selected_index]["Job ID"]
        
        st.divider()
        st.subheader(f"Job Details: {selected_job_id}")
        
        job = manager.get_job(selected_job_id)
        if job:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Status", job.status.value)
                st.metric("Results Found", job.total_results)
                
            with col2:
                st.progress(job.progress, text="Progress")
                if job.completed_at:
                    st.text(f"Completed: {job.completed_at}")
                if job.error:
                    st.error(f"Error: {job.error}")

            if job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
                if st.button("Cancel Job", type="primary"):
                    if manager.cancel_job(job.id):
                        st.success("Job cancellation requested.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to cancel job.")

            # Logs Expander
            with st.expander("Execution Logs", expanded=True):
                logs = manager.read_logs(job.id)
                st.code(logs, language="text")

            # Results Expander
            with st.expander("Search Results"):
                results = manager.get_job_results(job.id)
                if results:
                    st.dataframe(pd.DataFrame(results))
                else:
                    st.info("No results yet.")
        else:
            st.error("Could not load job details.")

# Auto-refresh logic using empty placeholder
if refresh_rate > 0:
    time.sleep(refresh_rate)
    st.rerun()
