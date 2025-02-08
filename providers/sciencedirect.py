import requests
from bs4 import BeautifulSoup
from providers.provider import Provider
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


class ScienceDirectProvider(Provider):
    # def fetch_html(self, url: str) -> str:
    #     headers = {
    #         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    #         "authority": "www.sciencedirect.com",
    #         "method": "GET",
    #         "path": "/",
    #         "scheme": "https",
    #         "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    #         "accept-encoding": "gzip, deflate, br, zstd",
    #         "accept-language": "en-US,en;q=0.9",
    #         "priority": "u=0, i",
    #         "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
    #         "sec-ch-ua-mobile": "?0",
    #         "sec-ch-ua-platform": '"Windows"',
    #         "sec-fetch-dest": "document",
    #         "sec-fetch-mode": "navigate",
    #         "sec-fetch-site": "none",
    #         "sec-fetch-user": "?1",
    #     }
    #     response = requests.get(url, headers=headers)
    #     response.raise_for_status()
    #     return response.text

    def fetch_html(self, url):
        return self.fetch_using_selenium(url)

    def get_abstract(self) -> str:
        abstract = self.soup.find("div", class_="abstract author")
        if abstract:
            return abstract.text.strip()
        else:
            raise Exception("Abstract not found")
