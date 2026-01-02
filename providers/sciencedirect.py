from providers.provider import Provider

class ScienceDirectProvider(Provider):
    def get_abstract(self) -> str:
        abstract = self.soup.find("div", class_="abstract author")
        if abstract:
            return abstract.text.strip()
        else:
            raise Exception("Abstract not found")
