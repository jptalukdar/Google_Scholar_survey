# Google Scholar Survey & SLR Workflow

An AI-powered system for Systematic Literature Reviews (SLR) using Google Scholar.

## Architecture

This project uses a client-server architecture:
- **Backend**: FastAPI server (`server/`) handling web scraping workers, job management, and AI processing.
- **Frontend**: Streamlit application (`home.py`, `pages/`) interacting with the backend via REST API.

## Features
- **Scalable Scraping**: Background workers for concurrent searches.
- **AI-Powered SLR**: 
    - Generate research questions from abstracts (Gemini).
    - Create complex boolean search queries.
    - Filter papers by relevance using AI.
- **Job Monitoring**: Real-time progress tracking and log streaming.
- **Data Export**: Download results as CSV or ZIP of PDFs.

## Installation

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Setup Selenium drivers (Chrome used by default):
   - Windows: Run `setup_selenium.bat`
   - Linux: Run `setup_selenium.sh`

### Running Backend and Frontend Separately

If you prefer to run them in separate terminals:

**Backend Only:**
```bash
python start_backend.py
# OR
run_backend.bat
```

**Frontend Only:**
```bash
python start_frontend.py
# OR
run_frontend.bat
```

- **Frontend**: http://localhost:8501
- **Backend API Docs**: http://localhost:8000/docs

## Configuration

- **API Keys**: Enter your Google Gemini API key in the Streamlit Sidebar.
- **Output**: Data is stored in `.data/` directory.

## Directory Structure
- `start_system.py`: Entry point.
- `server/`: FastAPI backend.
- `client/`: Python API client for frontend.
- `workers/`: Background job processing logic.
- `slr/`: Systematic Literature Review logic.
- `ai/`: LLM provider integration.
- `shared/`: Shared Pydantic schemas.

## Chrome Extension

The `slr-extension/` folder contains a browser extension for Google Scholar integration.

### Installation
1. Go to `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** → select `slr-extension/`

### Features
- **Assistant Tab**: Generate search queries from abstracts using AI
- **Database Tab**: Manage saved papers with status tracking
- **In-page buttons**: Add papers directly from Google Scholar results

## Data Export/Import

Transfer your papers and projects between machines:

```bash
# Export all data
python export_import_data.py export

# Export papers only (CSV)
python export_import_data.py export-csv

# Import on another machine
python export_import_data.py import slr_export_20260102.json

# View statistics
python export_import_data.py stats
```
