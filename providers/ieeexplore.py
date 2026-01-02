from providers.provider import Provider


class IEEEXplore(Provider):
    def get_abstract(self) -> str:
        abstract = self.soup.find("div", class_="abstract-text")
        if abstract:
            return abstract.text.strip()[9:]
        else:
            print(f"Abstract not found in {self.url}")
            return "Abstract not found"

    @staticmethod
    def download_url(title, url):
        return Provider.download_using_chrome(title, url)
