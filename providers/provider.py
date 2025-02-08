import requests
from bs4 import BeautifulSoup
import os
import hashlib
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

DATADIR = ".data/"

# Ensure the data directory exists
if not os.path.exists(DATADIR):
    os.makedirs(DATADIR)


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

    def fetch_using_selenium(self, url: str) -> str:
        options = Options()
        options.headless = True  # type: ignore
        driver = webdriver.Firefox(options=options)

        try:
            driver.get(url)
            html = driver.page_source
        finally:
            driver.quit()

        return html

    def get_soup(self, html: str) -> BeautifulSoup:
        """Parse the HTML content and return a BeautifulSoup object."""
        return BeautifulSoup(html, "html.parser")

    def get_html(self) -> BeautifulSoup:
        return self.get_soup(self.fetch_html(self.url))

    def get_html_cache(self) -> BeautifulSoup:
        # Create a hash of the URL
        url_hash = hashlib.md5(self.url.encode()).hexdigest()
        cache_file = os.path.join(DATADIR, f"{self.__class__.__name__}_{url_hash}.html")

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
        abstract = self.soup.find("div", class_=class_)
        if abstract:
            return abstract.text.strip()
        else:
            print(f"Abstract not found in {self.url}")
            return "Abstract not found"
