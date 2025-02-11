from typing import Tuple
import requests
from bs4 import BeautifulSoup
import os
import hashlib
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

DATADIR = ".data/"
SEARCH_DIR = os.path.join(DATADIR, "searches")
RESULTS_DIR = os.path.join(DATADIR, "results")
DOWNLOAD_DIR = os.path.join(DATADIR, "pdfs")
# Ensure the data directory exists
if not os.path.exists(DATADIR):
    os.makedirs(DATADIR)
    os.makedirs(SEARCH_DIR)
    os.makedirs(DOWNLOAD_DIR)
    os.makedirs(RESULTS_DIR)


class Provider:
    def __init__(self, url: str, cache: bool = False):
        self.url: str = url
        if cache:
            self.soup = self.get_html_cache()
        else:
            self.soup = self.get_html()

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__class__.__name__

    def __dict__(self):
        return {}

    def get_abstract(self) -> str:
        raise NotImplementedError(
            "You need to implement this method in your Provider subclass"
        )

    def fetch_html(self, url: str) -> str:
        """Fetch the HTML content of the given URL."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text

    @staticmethod
    def fetch_using_selenium(url: str) -> str:
        options = Options()
        options.headless = True  # type: ignore
        driver = webdriver.Firefox(options=options)

        try:
            driver.get(url)
            html = driver.page_source
        finally:
            driver.quit()

        return html

    @staticmethod
    def download_using_chrome(title, url) -> Tuple[bool, str]:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument(f"--user-agent={user_agent}")
        chrome_options.add_experimental_option(
            "prefs", {"download.default_directory": DOWNLOAD_DIR}
        )
        driver = webdriver.Chrome(options=chrome_options)
        try:
            driver.get(url)
            return True, driver.current_url
        except Exception as e:
            print(f"Error in {url}: {e}")
            return False, str(e)

    @staticmethod
    def download_using_firefox(title, url) -> Tuple[bool, str]:
        firefox_options = Options()
        firefox_options.headless = True  # type: ignore
        firefox_options.set_preference("browser.download.folderList", 2)
        firefox_options.set_preference(
            "browser.download.manager.showWhenStarting", False
        )
        firefox_options.set_preference("browser.download.dir", DOWNLOAD_DIR)
        firefox_options.set_preference(
            "browser.helperApps.neverAsk.saveToDisk",
            "application/octet-stream,application/pdf",
        )
        driver = webdriver.Firefox(options=firefox_options)

        try:
            driver.get(url)
            return True, driver.current_url
        except Exception as e:
            print(f"Error in {url}: {e}")
            return False, str(e)

    @staticmethod
    def download_pdf(title: str, url: str) -> Tuple[bool, str]:
        # url_hash = hashlib.md5(url.encode()).hexdigest()
        filename = (
            "".join(char for char in title if char.isascii())
            .replace(" ", "_")
            .replace(":", "-")
        )
        cache_file = os.path.join(DOWNLOAD_DIR, f"{filename}.pdf")
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(cache_file, "wb") as pdf_file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        pdf_file.write(chunk)
            print(f"Downloaded PDF to {cache_file}")
            return True, cache_file
        else:
            print(
                f"Failed to download PDF from {url} , {response.status_code}, {response.text}"
            )
            return False, cache_file

    def get_soup(self, html: str) -> BeautifulSoup:
        """Parse the HTML content and return a BeautifulSoup object."""
        return BeautifulSoup(html, "html.parser")

    def get_html(self) -> BeautifulSoup:
        return self.get_soup(self.fetch_html(self.url))

    def get_url_hash(self, url=None) -> str:
        if url is None:
            url = self.url
        return hashlib.md5(url.encode()).hexdigest()

    def get_html_cache(self) -> BeautifulSoup:
        # Create a hash of the URL
        url_hash = self.get_url_hash()
        cache_file = os.path.join(
            SEARCH_DIR, f"{self.__class__.__name__}_{url_hash}.html"
        )

        # Check if the file exists in the DATADIR
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as file:
                return self.get_soup(file.read())
        else:
            # Fetch using get_html and store in the DATADIR if data is returned successfully
            html_content = self.fetch_html(self.url)
            if html_content and len(html_content) > 30:
                with open(cache_file, "w", encoding="utf-8") as file:
                    file.write(html_content)
                return self.get_soup(html_content)
            else:
                print(html_content)
                raise ValueError("Failed to fetch HTML content")


class AbstractClassProvider(Provider):
    def get_abstract_by_class(self, class_=""):
        return self.get_abstract_by_element("div", class_)

    def get_abstract_by_element(self, element: str, class_=""):
        abstract = self.soup.find(element, class_=class_)
        if abstract:
            return abstract.text.strip()
        else:
            print(f"Abstract not found in {self.url}")
            return "Abstract not found"
