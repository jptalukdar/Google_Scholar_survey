import os
from bs4 import BeautifulSoup
from providers import *

SEARCH_DIR = ".data/searches"

HTML_FILES = []
for dirpath, dirnames, filenames in os.walk(SEARCH_DIR):
    print(dirpath)
    HTML_FILES = [
        (file, os.path.join(dirpath, file))
        for file in filenames
        if file.endswith(".html")
    ]


def parse_file(filepath):
    with open(filepath[1], "r", errors="ignore") as fp:
        data = fp.read()

    provider = filepath[0].split("_")[0]
    print(provider)
    soup = BeautifulSoup(data)
    return provider, soup


for file in HTML_FILES:
    provider, soup = parse_file(file)
