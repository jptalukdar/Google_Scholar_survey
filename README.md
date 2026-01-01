# Google Scholar Survey & Literature Review Tool

A scalable, worker-based system for automating literature reviews using Google Scholar and various academic databases. This tool allows you to perform background searches, scrape metadata, and download PDFs from supported providers.

## Features

- **Scalable Worker Architecture**: Runs searches in background threads, allowing for long-running jobs without blocking the UI.
- **Provider Support**: Specialized extractors for:
  - Google Scholar (Base)
  - ArXiv
  - ScienceDirect
  - IEEE Xplore
  - Springer Link
  - ACM Digital Library
  - Wiley Online Library
  - MDPI
  - Frontiers
- **Site Restrictions**: Filter searches to specific high-quality academic databases.
- **Job Management**:
  - Live progress tracking
  - Real-time log streaming
  - Job cancellation
  - Persistent result storage
- **Interactive UI**: Built with Streamlit for easy job submission and monitoring.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository_url>
   cd Google_Scholar_survey
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup WebDrivers**:
   This tool requires Selenium WebDrivers (Chrome or Firefox).
   - Ensure `chromedriver` or `geckodriver` is in your system PATH or placed in the `driver/` directory.
   - For Linux, run `./setup_selenium.sh` to download and setup the drivers. 
   - For Windows, run `setup_selenium.bat` to download and setup the drivers.

## Usage

### Web Interface (Streamlit)

1. **Start the application**:
   ```bash
   streamlit run home.py
   ```

2. **Submit a Search Job**:
   - Navigate to the **Home** page.
   - Enter your **Query**.
   - Configure parameters (Start index, Max results, Year).
   - (Optional) Select specific **Databases** to restrict your search.
   - Click **Submit Job**.

3. **Monitor Progress**:
   - Go to the **Job Monitor** page (sidebar).
   - View the list of active and completed jobs.
   - Select a job to see detailed progress, logs, and results.
   - Use the **Cancel Job** button to stop running searches.

### Programmatic API

You can use the `JobManager` API to integrate literature searches into other Python scripts.

```python
from api import JobManager

# Initialize manager
manager = JobManager()

# Submit a job
job_id = manager.submit_job(
    query="generative ai in education",
    start=0,
    max_results=50,
    since_year=2023,
    download_pdfs=True,
    sites=["sciencedirect.com", "arxiv.org"]
)

print(f"Job submitted: {job_id}")

# Get status
status = manager.get_job_status(job_id)
print(f"Status: {status}")
```

See `examples/example_client.py` for a complete example.

## Project Structure

- `core/`: Shared infrastructure (Config, Logging).
- `workers/`: Background worker system (Queue, Pool, Storage).
- `providers/`: Database-specific scrapers and PDF downloaders.
- `api/`: Public API for job management.
- `.data/`: Storage for results, logs, and downloaded PDFs.

## Notes

- **Rate Limiting**: Use responsibly. Frequent automated requests to Google Scholar may result in IP blocks / CAPTCHAs.
- **PDF Access**: Downloading PDFs (ScienceDirect, IEEE, etc.) often requires an active institutional subscription or VPN connection.

## Disclaimer

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
