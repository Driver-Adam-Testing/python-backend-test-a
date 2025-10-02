from utils.symbol_table.base import LanguageProvider
from utils.symbol_table.import_resolvers.go_resolver import GoResolver
from utils.symbol_table.symbol_parsers.go_parser import GoParser


class GoLanguageProvider(LanguageProvider):
    language = "go"

    @classmethod
    def get_parser(cls) -> GoParser:
        return GoParser()

    @classmethod
    def get_resolver(cls) -> GoResolver:
        return GoResolver()
