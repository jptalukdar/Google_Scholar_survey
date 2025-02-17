from providers.provider import Provider


class ACMProvider(Provider):
    def get_abstract(self):
        abstract = self.soup.find("section", id="abstract")
        if abstract:
            return abstract.text.strip()[8:]
        else:
            raise Exception("Abstract not found")
