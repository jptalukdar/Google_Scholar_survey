import os
import json

DIRECTORY = ".data/results"


def fetch_empty_provider_urls(directory):
    empty_provider_urls = []
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            with open(os.path.join(directory, filename), "r") as file:
                data = json.load(file)
                if "url" in data:
                    empty_provider_urls.append(data["url"])
    return empty_provider_urls


emptyProvider = fetch_empty_provider_urls(DIRECTORY)

domain_to_url = {}
for url in emptyProvider:
    domain = url.split("//")[-1].split("/")[0]
    domain_to_url[domain] = url

with open("provider_urls.json", "w") as file:
    json.dump(domain_to_url, file, indent=2)
