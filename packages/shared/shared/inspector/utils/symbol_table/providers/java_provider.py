from shared.inspector.utils.symbol_table.base import LanguageProvider
from shared.inspector.utils.symbol_table.import_resolvers.java_resolver import (
    JavaResolver,
)
from shared.inspector.utils.symbol_table.symbol_parsers.java_parser import JavaParser


class JavaLanguageProvider(LanguageProvider):
    language = "java"

    @classmethod
    def get_parser(cls) -> JavaParser:
        return JavaParser()

    @classmethod
    def get_resolver(cls) -> JavaResolver:
        return JavaResolver()
