import streamlit as st
import requests
from datetime import datetime

st.set_page_config(
    page_title="Extension Projects",
    page_icon="📚",
    layout="wide"
)

st.title("📚 Extension Projects & Papers")
st.markdown("View and manage papers collected from the Google Scholar extension.")

BACKEND_URL = "http://localhost:8000"

# --- API Helpers ---
def get_projects():
    try:
        response = requests.get(f"{BACKEND_URL}/extension/projects")
        if response.ok:
            return response.json()
    except:
        pass
    return []

def get_papers(project_id="default"):
    try:
        response = requests.get(f"{BACKEND_URL}/extension/papers", params={"project_id": project_id})
        if response.ok:
            return response.json()
    except:
        pass
    return []

def create_project(project_id, name, description=""):
    try:
        response = requests.post(f"{BACKEND_URL}/extension/projects", json={
            "id": project_id,
            "name": name,
            "description": description
        })
        return response.ok
    except:
        return False

def delete_paper(paper_id):
    try:
        response = requests.delete(f"{BACKEND_URL}/extension/papers/{paper_id}")
        return response.ok
    except:
        return False

# --- Health Check ---
try:
    health = requests.get(f"{BACKEND_URL}/health", timeout=2)
    if not health.ok:
        st.error("⚠️ Backend server is not responding. Please start it with `python start_backend.py`")
        st.stop()
except:
    st.error("⚠️ Cannot connect to backend server. Please start it with `python start_backend.py`")
    st.stop()

# --- Sidebar: Project Management ---
with st.sidebar:
    st.header("🗂️ Projects")
    
    projects = get_projects()
    project_names = {p["id"]: p["name"] for p in projects}
    
    if projects:
        selected_project = st.selectbox(
            "Select Project",
            options=[p["id"] for p in projects],
            format_func=lambda x: project_names.get(x, x)
        )
    else:
        selected_project = None
        st.info("No projects yet. Create one below!")
    
    st.divider()
    
    st.subheader("➕ New Project")
    with st.form("new_project_form"):
        new_id = st.text_input("Project ID", placeholder="my-review-2024")
        new_name = st.text_input("Project Name", placeholder="My Literature Review")
        new_desc = st.text_area("Description (optional)", placeholder="Notes about this project...")
        
        if st.form_submit_button("Create Project"):
            if new_id and new_name:
                if create_project(new_id, new_name, new_desc):
                    st.success(f"Project '{new_name}' created!")
                    st.rerun()
                else:
                    st.error("Failed to create project. ID may already exist.")
            else:
                st.warning("Please fill in ID and Name.")

# --- Main Content: Papers List ---
if selected_project:
    st.header(f"📄 Papers in: {project_names.get(selected_project, selected_project)}")
    
    papers = get_papers(selected_project)
    
    if not papers:
        st.info("No papers saved in this project yet. Use the Chrome extension on Google Scholar to add papers!")
    else:
        # Stats
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Papers", len(papers))
        with_pdf = sum(1 for p in papers if p.get("pdfUrl"))
        col2.metric("With PDF Link", with_pdf)
        col3.metric("Without PDF", len(papers) - with_pdf)
        
        st.divider()
        
        # Papers Table
        for i, paper in enumerate(papers):
            with st.container():
                cols = st.columns([0.05, 0.7, 0.15, 0.1])
                
                with cols[0]:
                    st.write(f"**{i+1}**")
                
                with cols[1]:
                    st.markdown(f"**{paper.get('title', 'Untitled')}**")
                    st.caption(f"Authors: {paper.get('authors', 'Unknown')}")
                    if paper.get('abstract'):
                        with st.expander("Abstract"):
                            st.write(paper['abstract'])
                
                with cols[2]:
                    if paper.get('url'):
                        st.link_button("🔗 View", paper['url'])
                    if paper.get('pdfUrl'):
                        st.link_button("📄 PDF", paper['pdfUrl'])
                
                with cols[3]:
                    if st.button("🗑️", key=f"del_{paper['id']}", help="Remove paper"):
                        if delete_paper(paper['id']):
                            st.rerun()
                
                st.divider()
        
        # Export Options
        st.subheader("📥 Export")
        col1, col2 = st.columns(2)
        
        with col1:
            # CSV Export
            import csv
            import io
            
            csv_buffer = io.StringIO()
            writer = csv.DictWriter(csv_buffer, fieldnames=["title", "authors", "url", "pdfUrl", "abstract"])
            writer.writeheader()
            for p in papers:
                writer.writerow({
                    "title": p.get("title", ""),
                    "authors": p.get("authors", ""),
                    "url": p.get("url", ""),
                    "pdfUrl": p.get("pdfUrl", ""),
                    "abstract": p.get("abstract", "")
                })
            
            st.download_button(
                "Download CSV",
                csv_buffer.getvalue(),
                file_name=f"{selected_project}_papers.csv",
                mime="text/csv"
            )
        
        with col2:
            # BibTeX Export (simplified)
            bibtex_entries = []
            for p in papers:
                title = p.get("title", "Unknown")
                authors = p.get("authors", "Unknown")
                url = p.get("url", "")
                entry_id = title.split()[0].lower() if title else "unknown"
                
                bibtex = f"""@article{{{entry_id},
  title = {{{title}}},
  author = {{{authors}}},
  url = {{{url}}}
}}"""
                bibtex_entries.append(bibtex)
            
            st.download_button(
                "Download BibTeX",
                "\n\n".join(bibtex_entries),
                file_name=f"{selected_project}_papers.bib",
                mime="text/plain"
            )

else:
    st.info("Select or create a project from the sidebar to view papers.")
