from utils.symbol_table.base import LanguageProvider
from utils.symbol_table.import_resolvers.csharp_resolver import CSharpResolver
from utils.symbol_table.symbol_parsers.csharp_parser import CSharpParser


class CSharpLanguageProvider(LanguageProvider):
    language = "csharp"

    @classmethod
    def get_parser(cls) -> CSharpParser:
        return CSharpParser()

    @classmethod
    def get_resolver(cls) -> CSharpResolver:
        return CSharpResolver()
