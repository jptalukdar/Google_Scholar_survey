from providers.provider import Provider


class ArxivProvider(Provider):
    # def download_pdf(self) -> str:

    def get_abstract(self) -> str:
        abstract = self.soup.find("blockquote", class_="abstract mathjax")
        if abstract:
            return abstract.text.strip()[9:]
        else:
            raise Exception("Abstract not found")
