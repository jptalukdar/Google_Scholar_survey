from providers.provider import Provider


class SpringerProvider(Provider):
    def get_abstract(self) -> str:
        abstract = self.soup.find("div", id="Abs1-content")
        if abstract:
            return abstract.text.strip()
        else:
            print(f"Abstract not found in {self.url}")
            return "Abstract not found"
