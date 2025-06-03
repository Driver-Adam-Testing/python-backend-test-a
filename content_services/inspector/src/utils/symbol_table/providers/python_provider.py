from utils.symbol_table.base import LanguageProvider
from utils.symbol_table.import_resolvers.python_resolver import PythonResolver
from utils.symbol_table.symbol_parsers.python_parser import PythonParser


class PythonLanguageProvider(LanguageProvider):
    language = "python"

    @classmethod
    def get_parser(cls) -> PythonParser:
        return PythonParser()

    @classmethod
    def get_resolver(cls) -> PythonResolver:
        return PythonResolver()  # pass tree as arg! just take class TODO!
