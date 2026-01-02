import streamlit as st
import pandas as pd
import time
import os
import json
from client import ApiClient

st.set_page_config(page_title="SLR Wizard", page_icon="📚", layout="wide")

# Sidebar - API Key Configuration
st.sidebar.title("🔑 AI Configuration")
st.sidebar.markdown("""
Enter your Gemini API key to enable AI features.

**[Get your API key here →](https://aistudio.google.com/app/apikey)**
""")

api_key = st.sidebar.text_input(
    "Gemini API Key",
    type="password",
    help="Your Google AI Studio API key for Gemini"
)

if not api_key:
    st.sidebar.warning("Please enter an API key to use the SLR Wizard.")

provider = st.sidebar.selectbox(
    "LLM Provider",
    options=["gemini"],
    help="More providers coming soon (Ollama, OpenAI)"
)

st.sidebar.divider()

# Site restrictions
DEFAULT_SITES = [
    "sciencedirect.com",
    "ieeexplore.ieee.org", 
    "link.springer.com",
    "dl.acm.org",
    "onlinelibrary.wiley.com",
    "arxiv.org"
]

selected_sites = st.sidebar.multiselect(
    "Restrict to Databases",
    options=DEFAULT_SITES,
    default=[],
    help="Leave empty to search all sources"
)

# Initialize Client
if 'api_client' not in st.session_state:
    st.session_state.api_client = ApiClient()

client = st.session_state.api_client

# Main content
st.title("📚 Systematic Literature Review Wizard (Client-Server)")

# Initialize session state
if "slr_step" not in st.session_state:
    st.session_state.slr_step = 1
if "research_questions" not in st.session_state:
    st.session_state.research_questions = None
if "queries" not in st.session_state:
    st.session_state.queries = None
if "job_ids" not in st.session_state:
    st.session_state.job_ids = None
if "results" not in st.session_state:
    st.session_state.results = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Step indicator
steps = ["Input Abstract", "Research Questions", "Search Queries", "Execute Search", "Results"]
cols = st.columns(len(steps))
for i, (col, step) in enumerate(zip(cols, steps)):
    if i + 1 < st.session_state.slr_step:
        col.success(f"✅ {step}")
    elif i + 1 == st.session_state.slr_step:
        col.info(f"👉 {step}")
    else:
        col.write(f"⬜ {step}")

st.divider()

# Step 1: Input Abstract
if st.session_state.slr_step == 1:
    st.subheader("Step 1: Enter Your Research Topic")
    
    abstract = st.text_area(
        "Research Abstract or Topic Description",
        height=200,
        placeholder="Paste your research abstract..."
    )
    
    if st.button("Generate Questions →", type="primary", disabled=not api_key or not abstract):
        with st.spinner("Generating research questions..."):
            try:
                questions = client.generate_questions(abstract, api_key, provider)
                st.session_state.research_questions = questions
                st.session_state.abstract = abstract
                st.session_state.slr_step = 2
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# Step 2: Research Questions
elif st.session_state.slr_step == 2:
    st.subheader("Step 2: Review & Refine Research Questions")
    
    questions = st.session_state.research_questions
    
    st.info(f"**Topic:** {questions['topic']}")
    
    st.markdown("### Generated Research Questions")
    for rq in questions['questions']:
        st.markdown(f"**{rq}**")
    
    st.markdown("### Keywords")
    st.write(", ".join(questions['keywords']))
    
    st.divider()
    
    # Chat refinement
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
    if feedback := st.chat_input("Refine questions..."):
        st.session_state.chat_history.append({"role": "user", "content": feedback})
        
        with st.spinner("Refining questions..."):
            try:
                updated = client.refine_questions(questions, feedback, api_key, provider)
                st.session_state.research_questions = updated
                st.session_state.chat_history.append({
                    "role": "assistant", 
                    "content": f"Updated questions:\n" + "\n".join(updated['questions'])
                })
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Back"): st.session_state.slr_step = 1; st.rerun()
    with col2:
        if st.button("Generate Queries →"):
            with st.spinner("Generating..."):
                try:
                    qs = client.generate_queries(questions, selected_sites, api_key, provider)
                    st.session_state.queries = qs
                    st.session_state.slr_step = 3
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# Step 3: Queries
elif st.session_state.slr_step == 3:
    st.subheader("Step 3: Review Search Queries")
    
    queries = st.session_state.queries
    edited_queries = []
    
    for i, q in enumerate(queries):
        val = st.text_input(f"Query {i+1}", value=q['query'], key=f"q_{i}")
        q['query'] = val
        edited_queries.append(q)
    
    st.session_state.queries = edited_queries
    
    st.divider()
    max_results = st.number_input("Max Results", value=20)
    since_year = st.number_input("Since Year", value=2020)
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Back"): st.session_state.slr_step = 2; st.rerun()
    with col2:
        if st.button("Execute Search →"):
            with st.spinner("Starting jobs..."):
                try:
                    job_ids = []
                    # We need to format the query (add site:) as client logic if not done by server
                    # The server's submit_job takes 'sites' list and handles it? 
                    # Checking schemas: submit_job takes 'sites'. Yes.
                    
                    for q in queries:
                        # Construct site string if needed or pass list
                        # q['sites'] has sites. submit_job takes sites. 
                        # Ideally server does logic, but we formatted generic query.
                        # We will pass q['query'] and q['sites'] to submit_job
                         
                        jid = client.submit_job(
                            q['query'], 
                            max_results, 
                            since_year, 
                            q.get('sites', []),
                            download_pdfs=False
                        )
                        job_ids.append(jid)
                    
                    st.session_state.job_ids = job_ids
                    st.session_state.slr_config = {
                        "max_results": max_results,
                        "since_year": since_year
                    }
                    st.session_state.slr_step = 4
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# Step 4: Execute
elif st.session_state.slr_step == 4:
    st.subheader("Step 4: Executing Search")
    
    all_done = False
    placeholder = st.empty()
    
    while not all_done:
        all_done = True
        status_data = []
        
        for jid in st.session_state.job_ids:
            job = client.get_job(jid)
            if job:
                status_data.append(job)
                if job['status'] not in ["completed", "failed", "cancelled"]:
                    all_done = False
        
        with placeholder.container():
            st.dataframe(pd.DataFrame(status_data)[['id', 'status', 'progress', 'total_results']])
        
        if not all_done:
            time.sleep(2)
            st.rerun()
    
    if st.button("Filter by Relevance →"):
        st.session_state.slr_step = 5
        st.rerun()

# Step 5: Results
elif st.session_state.slr_step == 5:
    st.subheader("Results")
    
    if not st.session_state.results:
        with st.spinner("Filtering..."):
            try:
                # Collect ALL papers
                all_papers = []
                seen = set()
                for jid in st.session_state.job_ids:
                    job = client.get_job(jid)
                    if job and 'results' in job:
                        for p in job['results']:
                            if p.get('title') not in seen:
                                seen.add(p.get('title'))
                                all_papers.append(p)
                
                # Filter
                res = client.filter_relevance(
                    all_papers, 
                    st.session_state.research_questions['questions'],
                    6,
                    api_key, provider
                )
                st.session_state.results = res
                st.session_state.results['all'] = all_papers # Store original too
            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()
    
    res = st.session_state.results
    st.metric("Relevant Papers", len(res['included']))
    
    st.dataframe(pd.DataFrame(res['included']))
    
    # Download
    if st.button("Download PDFs"):
        with st.spinner("Downloading..."):
            path = client.download_pdfs(res['included'], "slr_export")
            if path:
                st.success(f"Downloaded to {path}")
            else:
                st.warning("No PDFs found")
