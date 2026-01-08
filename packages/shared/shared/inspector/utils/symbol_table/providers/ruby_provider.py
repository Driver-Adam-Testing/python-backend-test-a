from shared.inspector.utils.symbol_table.base import LanguageProvider
from shared.inspector.utils.symbol_table.import_resolvers.ruby_resolver import (
    RubyResolver,
)
from shared.inspector.utils.symbol_table.symbol_parsers.ruby_parser import RubyParser


class RubyLanguageProvider(LanguageProvider):
    language = "ruby"

    @classmethod
    def get_parser(cls) -> RubyParser:
        return RubyParser()

    @classmethod
    def get_resolver(cls) -> RubyResolver:
        return RubyResolver()
