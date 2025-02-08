from providers.provider import Provider


class EmptyProvider(Provider):
    def __init__(self, url, cache=False):
        self.url = url
        self.cache = cache

    def get_abstract(self) -> str:
        return "Abstract not found"
