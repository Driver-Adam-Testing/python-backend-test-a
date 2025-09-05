from utils.symbol_table_v2.base import LanguageProvider
from utils.symbol_table_v2.import_resolvers.csharp_resolver import CSharpResolver
from utils.symbol_table_v2.symbol_parsers.csharp_parser import CSharpParser


class CSharpLanguageProvider(LanguageProvider):
    language = "csharp"

    @classmethod
    def get_parser(cls) -> CSharpParser:
        return CSharpParser()

    @classmethod
    def get_resolver(cls) -> CSharpResolver:
        return CSharpResolver()
