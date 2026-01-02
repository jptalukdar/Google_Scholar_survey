import streamlit as st
import pandas as pd
import time
import os
import json
from client import ApiClient
from shared.ui import sidebar_api_key

st.set_page_config(page_title="SLR Wizard", page_icon="📚", layout="wide")

# Sidebar - API Key Configuration
api_key = sidebar_api_key()

provider = st.sidebar.selectbox(
    "LLM Provider",
    options=["gemini"],
    help="More providers coming soon (Ollama, OpenAI)"
)

st.sidebar.divider()

# --- Session Management ---
st.sidebar.header("📂 Session")

# Initialize session metadata
if "session_name" not in st.session_state:
    st.session_state.session_name = f"SLR_{int(time.time())}"
if "session_created_at" not in st.session_state:
    st.session_state.session_created_at = time.strftime("%Y-%m-%d %H:%M:%S")

# Session Naming
st.session_state.session_name = st.sidebar.text_input(
    "Session Name", 
    value=st.session_state.session_name,
    help="Name your session for easier identification in exports"
)

# Resume Session
uploaded_file = st.sidebar.file_uploader(
    "📤 Resume Session",
    type=["json"],
    help="Upload a previously exported session JSON file"
)

if uploaded_file is not None:
    try:
        loaded_state = json.load(uploaded_file)
        # Basic validation
        if "slr_step" in loaded_state:
            for key, value in loaded_state.items():
                st.session_state[key] = value
            st.toast(f"Session '{st.session_state.session_name}' loaded successfully!")
            time.sleep(1)
            st.rerun()
        else:
            st.sidebar.error("Invalid session file.")
    except Exception as e:
        st.sidebar.error(f"Error loading session: {e}")

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
if "abstract" not in st.session_state:
    st.session_state.abstract = ""
if "research_questions" not in st.session_state:
    st.session_state.research_questions = None
if "queries" not in st.session_state:
    st.session_state.queries = None
if "max_results" not in st.session_state:
    st.session_state.max_results = 20
if "since_year" not in st.session_state:
    st.session_state.since_year = 2020
if "job_ids" not in st.session_state:
    st.session_state.job_ids = None
if "results" not in st.session_state:
    st.session_state.results = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Step indicator
# Step indicator
steps = ["Input Abstract", "Research Questions", "Search Queries", "Execute Search", "Results"]
cols = st.columns(len(steps))

for i, (col, step) in enumerate(zip(cols, steps)):
    step_num = i + 1
    if step_num < st.session_state.slr_step:
        # Make completed steps clickable
        if col.button(f"✅ {step}", key=f"nav_step_{i}"):
            st.session_state.slr_step = step_num
            st.rerun()
    elif step_num == st.session_state.slr_step:
        col.info(f"👉 {step}")
    else:
        col.write(f"⬜ {step}")

st.divider()

# Step 1: Input Abstract
if st.session_state.slr_step == 1:
    st.subheader("Step 1: Enter Your Research Topic")
    
    abstract = st.text_area(
        "Research Abstract or Topic Description",
        value=st.session_state.abstract,
        height=200,
        placeholder="Paste your research abstract..."
    )
    st.session_state.abstract = abstract
    
    if st.button("Generate Questions →", type="primary", disabled=not api_key or not abstract):
        with st.spinner("Generating research questions..."):
            try:
                questions = client.generate_questions(abstract, api_key, provider)
                st.session_state.research_questions = questions
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
    # We need to iterate over a copy or by index to safely modify the list if needed
    # But for Streamlit, reruns handle the state update.
    
    # Render existing queries with delete buttons
    indices_to_remove = []
    
    for i, q in enumerate(queries):
        col_q, col_del = st.columns([10, 1])
        with col_q:
            val = st.text_input(f"Query {i+1}", value=q['query'], key=f"q_{i}", label_visibility="collapsed")
            queries[i]['query'] = val
        with col_del:
            if st.button("🗑️", key=f"del_q_{i}", help="Remove this query"):
                indices_to_remove.append(i)
    
    # Process removals
    if indices_to_remove:
        for index in sorted(indices_to_remove, reverse=True):
            del st.session_state.queries[index]
        st.rerun()
        
    # Add new query button
    if st.button("➕ Add Query"):
        st.session_state.queries.append({"query": "", "sites": selected_sites})
        st.rerun()
    
    st.divider()
    max_results = st.number_input("Max Results", value=st.session_state.max_results)
    since_year = st.number_input("Since Year", value=st.session_state.since_year)
    st.session_state.max_results = max_results
    st.session_state.since_year = since_year
    
    col1, col2, col3 = st.columns([1, 2, 3])
    with col1:
        if st.button("Back"): st.session_state.slr_step = 2; st.rerun()
    with col2:
        if st.button("Regenerate Queries 🔄"):
            with st.spinner("Regenerating..."):
                try:
                    qs = client.generate_queries(st.session_state.research_questions, selected_sites, api_key, provider)
                    st.session_state.queries = qs
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    with col3:
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
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Back"): st.session_state.slr_step = 3; st.rerun()
    with col2:
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
    
    # --- Advanced Exports ---
    st.markdown("### 📤 Exports")
    
    # 1. Methodology Report
    def generate_methodology_report():
        report = f"""# Systematic Literature Review Methodology Report

## Session: {st.session_state.session_name}
**Date:** {time.strftime("%Y-%m-%d %H:%M:%S")}

---

## 1. Research Topic
{st.session_state.abstract}

---

## 2. Research Questions
"""
        if st.session_state.research_questions:
            for i, rq in enumerate(st.session_state.research_questions.get('questions', []), 1):
                report += f"{i}. {rq}\n"
            
            report += f"\n**Keywords:** {', '.join(st.session_state.research_questions.get('keywords', []))}\n"

        report += """
---

## 3. Search Strategy
"""
        if st.session_state.queries:
            report += "### Search Queries\n"
            for i, q in enumerate(st.session_state.queries, 1):
                report += f"{i}. `{q['query']}`\n"
        
        report += f"""
### Parameters
- **Since Year:** {st.session_state.since_year}
- **Max Results/Query:** {st.session_state.max_results}
- **Sources:** {', '.join(selected_sites) if selected_sites else 'All'}

---

## 4. Screening Results
| Metric | Count |
|--------|-------|
| Total Papers Retrieved | {len(res.get('all', []))} |
| Papers Included (Relevant) | {len(res['included'])} |
| Papers Excluded | {len(res.get('excluded', []))} |

---

## 5. Included Papers
| Title | Authors | URL |
|-------|---------|-----|
"""
        for paper in res['included']:
            t = paper.get('title', 'N/A').replace('|', '-')
            a = paper.get('author', 'N/A').replace('|', '-')
            u = paper.get('url', 'N/A')
            report += f"| {t} | {a} | [Link]({u}) |\n"
            
        return report

    col_exp1, col_exp2, col_exp3 = st.columns(3)
    
    with col_exp1:
        # CSV Export
        results_df = pd.DataFrame(res['included'])
        csv_data = results_df.to_csv(index=False)
        st.download_button(
            "📊 Download Results CSV",
            csv_data,
            file_name=f"{st.session_state.session_name}_results.csv",
            mime="text/csv"
        )
        
    with col_exp2:
        # Markdown Report
        report_md = generate_methodology_report()
        st.download_button(
            "📝 Download Report (MD)",
            report_md,
            file_name=f"{st.session_state.session_name}_report.md",
            mime="text/markdown",
            help="Full methodology report suitable for papers"
        )

    with col_exp3:
        # All Papers Export
        if res.get('all'):
            all_data = pd.DataFrame(res['all'])
            st.download_button(
                "📦 Download All (Pre-filter)",
                all_data.to_csv(index=False),
                file_name=f"{st.session_state.session_name}_all_papers.csv",
                mime="text/csv"
            )
    
    st.divider()
    if st.button("Back"): st.session_state.slr_step = 4; st.rerun()
    
    # Download
    if st.button("Download PDFs"):
        with st.spinner("Downloading..."):
            path = client.download_pdfs(res['included'], "slr_export")
            if path:
                st.success(f"Downloaded to {path}")
            else:
                st.warning("No PDFs found")

# --- Sidebar state export ---
st.sidebar.divider()
st.sidebar.subheader("💾 Session Management")

# Function to prepare state as JSON
def get_wizard_state():
    state = {
        key: st.session_state[key]
        for key in [
            "session_name", "session_created_at",
            "slr_step", "abstract", "research_questions", "queries", 
            "max_results", "since_year", "job_ids", "chat_history", "results"
        ]
        if key in st.session_state
    }
    state["exported_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    return state

wizard_json = json.dumps(get_wizard_state(), indent=2)
st.sidebar.download_button(
    "📥 Download State JSON",
    wizard_json,
    file_name=f"{st.session_state.get('session_name', 'session')}_{int(time.time())}.json",
    mime="application/json",
    help="Download everything including your research questions and generated queries."
)

if st.sidebar.button("🗑️ Reset Wizard"):
    keys_to_reset = ["slr_step", "abstract", "research_questions", "queries", "job_ids", "results", "chat_history"]
    for k in keys_to_reset:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()
