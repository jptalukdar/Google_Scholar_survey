from urllib.parse import urlparse

from providers import *
import streamlit as st
import os
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
import requests


def get_domain(url) -> str:
    """Extract the domain from the URL."""

    parsed_url = urlparse(url)
    return parsed_url.netloc


def file_exists(title) -> bool:
    """Check if a file with the given title exists in the download directory."""
    file_path = os.path.join(DOWNLOAD_DIR, f"{title}.pdf")
    return os.path.isfile(file_path)


def download_using_firefox_selenium(title, url) -> Tuple[bool, str]:
    firefox_options = FirefoxOptions()
    # firefox_options.headless = True  # type: ignore
    # firefox_options.set_preference("browser.download.folderList", 2)
    # firefox_options.set_preference("browser.download.manager.showWhenStarting", False)
    # firefox_options.set_preference("browser.download.dir", DOWNLOAD_DIR)
    firefox_options.set_preference(
        "browser.helperApps.neverAsk.saveToDisk",
        "application/pdf, application/x-pdf",
    )
    # firefox_options.set_preference("pdfjs.disabled", True)
    DOWNLOAD_DIR_ABS = os.path.abspath(DOWNLOAD_DIR)
    firefox_options.set_preference("browser.download.dir", DOWNLOAD_DIR_ABS)
    firefox_options.set_preference("browser.download.useDownloadDir", True)
    firefox_options.set_preference("browser.download.folderList", 2)
    firefox_options.set_preference("browser.download.manager.showWhenStarting", False)
    firefox_options.set_preference(
        "browser.helperApps.neverAsk.saveToDisk", "application/pdf"
    )
    firefox_options.set_preference("pdfjs.disabled", True)
    firefox_options.set_preference("browser.download.dir", DOWNLOAD_DIR_ABS)
    firefox_options.set_preference("browser.download.panel.shown", False)
    firefox_options.set_preference(
        "browser.download.manager.showAlertOnComplete", False
    )
    firefox_options.set_preference("browser.download.manager.closeWhenDone", True)
    driver = webdriver.Firefox(options=firefox_options)

    # try:
    driver.get(url)
    # finally:
    # driver.quit()

    if file_exists(title):
        status = True
    else:
        status = False
    return status, url


def download_using_chrome(title, url) -> Tuple[bool, str]:
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"

    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument(f"--user-agent={user_agent}")
    chrome_options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": DOWNLOAD_DIR,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.plugins_disabled": ["Chrome PDF Viewer"],
        },
    )
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get(url)
        if file_exists(title):
            status = True
        else:
            status = False
        return status, url
        # return True, driver.current_url
    except Exception as e:
        print(f"Error in {url}: {e}")
        return False, str(e)


def download_using_requests(title, url) -> Tuple[bool, str]:
    firefox_options = FirefoxOptions()
    firefox_options.headless = True
    driver = webdriver.Firefox(options=firefox_options)
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    try:
        driver.get(url)
        cookies = driver.get_cookies()
        # headers = driver.execute_script("return navigator.userAgent;")
        driver.quit()

        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(cookie["name"], cookie["value"])

        headers = {"User-Agent": user_agent}
        response = session.get(url, headers=headers, stream=True)
        filename = Provider.generate_filename(title)
        if response.status_code == 200:
            file_path = os.path.join(DOWNLOAD_DIR, f"{filename}.pdf")
            with open(file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            return True, url
        else:
            print(response.text)
            return False, f"Failed to download file: {response.status_code}"
    except Exception as e:
        return False, str(e)


st.title("File Downloader")

url = st.text_input("Enter the URL of the file:")
title = st.text_input("Enter the title of the file:")

if st.button("Download using Firefox"):
    if url and title:
        success, message = download_using_firefox_selenium(title, url)

        if success:
            st.success(f"File downloaded successfully from {message}")
        else:
            st.error("Failed to download the file.")
    else:
        st.warning("Please enter both URL and title.")

if st.button("Download using Chrome"):
    if url and title:
        success, message = download_using_chrome(title, url)

        if success:
            st.success(f"File downloaded successfully from {message}")
        else:
            st.error("Failed to download the file.")
    else:
        st.warning("Please enter both URL and title.")

if st.button("Download using Requests"):
    if url and title:
        success, message = download_using_requests(title, url)

        if success:
            st.success(f"File downloaded successfully from {message}")
        else:
            st.error(f"Failed to download the file. Exception {message}")
    else:
        st.warning("Please enter both URL and title.")
