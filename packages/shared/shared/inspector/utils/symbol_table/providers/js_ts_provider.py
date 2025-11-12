from shared.inspector.utils.symbol_table.base import LanguageProvider
from shared.inspector.utils.symbol_table.import_resolvers.js_ts_resolver import (
    JsTsResolver,
)
from shared.inspector.utils.symbol_table.symbol_parsers.js_ts_parser import JsTsParser


class JsTsLanguageProvider(LanguageProvider):
    language = "js_ts"

    @classmethod
    def get_parser(cls) -> JsTsParser:
        return JsTsParser()

    @classmethod
    def get_resolver(cls) -> JsTsResolver:
        return JsTsResolver()
