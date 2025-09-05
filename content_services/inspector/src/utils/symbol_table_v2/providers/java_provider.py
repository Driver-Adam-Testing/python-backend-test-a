from utils.symbol_table_v2.base import LanguageProvider
from utils.symbol_table_v2.import_resolvers.java_resolver import JavaResolver
from utils.symbol_table_v2.symbol_parsers.java_parser import JavaParser


class JavaLanguageProvider(LanguageProvider):
    language = "java"

    @classmethod
    def get_parser(cls) -> JavaParser:
        return JavaParser()

    @classmethod
    def get_resolver(cls) -> JavaResolver:
        return JavaResolver()
