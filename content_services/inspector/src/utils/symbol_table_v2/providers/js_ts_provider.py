from utils.symbol_table_v2.base import LanguageProvider
from utils.symbol_table_v2.import_resolvers.js_ts_resolver import JsTsResolver
from utils.symbol_table_v2.symbol_parsers.js_ts_parser import JsTsParser


class JsTsLanguageProvider(LanguageProvider):
    language = "js_ts"

    @classmethod
    def get_parser(cls) -> JsTsParser:
        return JsTsParser()

    @classmethod
    def get_resolver(cls) -> JsTsResolver:
        return JsTsResolver()
