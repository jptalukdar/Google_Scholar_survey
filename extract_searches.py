from functools import cache
import json
from urllib.parse import urlparse

import requests
from providers import *
import os
from providers.provider import Provider
from json import JSONEncoder


class StdWriter:
    def write(self, text):
        print(text)


class StreamlitWriter:
    def __init__(self, st):
        self.st = st

    def write(self, text):
        self.st.write(text)


class DefaultEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__


class GoogleScholarProvider(Provider):
    def parse_results(self, entry):
        title = entry.find("h3", class_="gs_rt").text
        url = (
            entry.find("h3", class_="gs_rt").a["href"]
            if entry.find("h3", class_="gs_rt") is not None
            else None
        )
        gg_ = entry.find("div", class_="gs_or_ggsm")
        download_link = gg_.a["href"] if gg_ is not None else None
        author = entry.find("div", class_="gs_a").text
        snippet = (
            entry.find("div", class_="gs_rs").text
            if entry.find("div", class_="gs_rs") is not None
            else None
        )
        try:
            provider = ParseProvider(url, cache=True)
        except Exception as e:
            print(f"Error in {url}: {e}")
            provider = EmptyProvider(url, cache=True)
        except requests.exceptions.HTTPError as e:
            print(f"Error in {url}: {e}")
            provider = EmptyProvider(url, cache=True)
        return {
            "title": title,
            "author": author,
            "url": url,
            "download_url": download_link,
            "snippet": snippet,
            "provider": provider.__class__.__name__,
            "provider_class": provider,
            "abstract": provider.get_abstract(),
        }

    def get_all_papers(self, writer=StdWriter):
        papers = []
        for entry in self.soup.find_all("div", class_="gs_r gs_or gs_scl"):
            res = self.parse_results(entry)
            writer.write(res)
            papers.append(res)
        return papers


def get_domain(url) -> str:
    """Extract the domain from the URL."""

    parsed_url = urlparse(url)
    return parsed_url.netloc


def ParseProvider(url, cache: bool = False):
    domain = get_domain(url)
    match domain:
        case "www.sciencedirect.com":
            return ScienceDirectProvider(url, cache)
        case "arxiv.org":
            return ArxivProvider(url, cache)
        case "ieeexplore.ieee.org":
            return IEEEXplore(url, cache)
        case "link.springer.com":
            return SpringerProvider(url, True)
        case "www.mdpi.com":
            return MDPI(url, cache)
        case "onlinelibrary.wiley.com":
            return Wiley(url, cache)
        case "www.frontiersin.org":
            return Frontiers(url, cache)
        case _:
            return EmptyProvider(url, cache)


def main():
    current_dir = os.path.abspath(os.getcwd())
    driver_bin = os.path.join(current_dir, "driver")
    os.environ["PATH"] += os.pathsep + driver_bin
    url = "https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&q=understanding+self+sovereign+identity&btnG="
    provider = GoogleScholarProvider(url, cache=True)
    papers = provider.get_all_papers()
    with open("papers.json", "w") as f:
        json.dump(papers, f, indent=4, cls=DefaultEncoder)
    for paper in papers:
        print(paper)


if __name__ == "__main__":
    main()
