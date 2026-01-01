import streamlit as st
import pandas as pd
import os
from api import JobManager

current_dir = os.path.abspath(os.getcwd())
driver_bin = os.path.join(current_dir, "driver")
# Ensure driver is in path if needed by local selenium
if driver_bin not in os.environ["PATH"]:
    os.environ["PATH"] += os.pathsep + driver_bin

def main():
    st.set_page_config(page_title="Scholar Downloader", layout="wide")
    st.title("Google Scholar Search Job Submitter")

    st.markdown("""
    Submit a background job to search Google Scholar and download PDFs.
    You can track progress in the **Job Monitor** page.
    """)

    query = st.text_input("Enter Query")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start = st.number_input("Start Index", min_value=0, max_value=1000, value=0)
    with col2:
        max_results = st.number_input("Max Results", min_value=10, max_value=1000, value=20, step=10)
    with col3:
        step = st.number_input("Step (Batch Size)", min_value=1, value=10)
        
    since_year = st.number_input("Since Year", min_value=1900, max_value=2025, value=2020)
    download_pdfs = st.checkbox("Download PDFs if available")

    # Site Restriction
    DEFAULT_SITES = [
        "sciencedirect.com",
        "ieeexplore.ieee.org",
        "link.springer.com",
        "dl.acm.org",
        "onlinelibrary.wiley.com",
        "mdpi.com",
        "frontiersin.org",
        "arxiv.org"
    ]
    
    selected_sites = st.multiselect(
        "Restrict to Specific Databases (Leave empty to search all)",
        options=DEFAULT_SITES,
        default=[]
    )

    if st.button("Submit Job", type="primary"):
        if not query:
            st.error("Please enter a query.")
        else:
            manager = JobManager()
            job_id = manager.submit_job(
                query=query,
                start=start,
                max_results=max_results,
                step=step,
                since_year=since_year,
                download_pdfs=download_pdfs,
                sites=selected_sites
            )
            
            st.success(f"Job submitted successfully! Job ID: `{job_id}`")
            st.info("Navigate to the **Job Monitor** page to track this job.")
            
            # Optional: Link to monitor page (hacky in Streamlit, better to just tell user)
            st.markdown("[Go to Job Monitor](/job_monitor)")

if __name__ == "__main__":
    main()
