from providers.provider import Provider


class IEEEXplore(Provider):
    def get_abstract(self) -> str:
        abstract = self.soup.find("div", class_="abstract-text")
        if abstract:
            return abstract.text.strip()
        else:
            print(f"Abstract not found in {self.url}")
            return "Abstract not found"

    def fetch_html(self, url):
        return self.fetch_using_selenium(url)
