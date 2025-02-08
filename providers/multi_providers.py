from providers.provider import AbstractClassProvider


class Wiley(AbstractClassProvider):
    def get_abstract(self):
        return super().get_abstract_by_class("article-section__content en main")


class Frontiers(AbstractClassProvider):
    def get_abstract(self):
        return super().get_abstract_by_class("JournalAbstract")


class MDPI(AbstractClassProvider):
    def get_abstract(self):
        return super().get_abstract_by_class("html-abstract")
