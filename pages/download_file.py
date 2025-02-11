from urllib.parse import urlparse

from providers import *
import streamlit as st
import os


def get_domain(url) -> str:
    """Extract the domain from the URL."""

    parsed_url = urlparse(url)
    return parsed_url.netloc


def download_using_selenium(title, url) -> Tuple[bool, str]:
    firefox_options = Options()
    # firefox_options.headless = True  # type: ignore
    firefox_options.set_preference("browser.download.folderList", 2)
    firefox_options.set_preference("browser.download.manager.showWhenStarting", False)
    firefox_options.set_preference("browser.download.dir", DOWNLOAD_DIR)
    firefox_options.set_preference(
        "browser.helperApps.neverAsk.saveToDisk",
        "application/pdf, application/x-pdf",
    )
    driver = webdriver.Firefox(options=firefox_options)

    # try:
    driver.get(url)
    # finally:
    # driver.quit()

    def file_exists(title) -> bool:
        """Check if a file with the given title exists in the download directory."""
        file_path = os.path.join(DOWNLOAD_DIR, f"{title}.pdf")
        return os.path.isfile(file_path)

    if file_exists(title):
        status = True
    else:
        status = False
    return status, url


st.title("File Downloader")

url = st.text_input("Enter the URL of the file:")
title = st.text_input("Enter the title of the file:")

if st.button("Download"):
    if url and title:
        success, download_url = download_using_selenium(title, url)

        if success:
            st.success(f"File downloaded successfully from {download_url}")
        else:
            st.error("Failed to download the file.")
    else:
        st.warning("Please enter both URL and title.")
