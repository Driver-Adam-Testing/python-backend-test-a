from utils.symbol_table.base import LanguageProvider
from utils.symbol_table.import_resolvers.python_resolver import PythonResolver
from utils.symbol_table.symbol_parsers.python_parser import PythonParser
from utils.treesitter_drivers.python_driver import PyDriverTree


class PythonLanguageProvider(LanguageProvider):
    language = "python"

    @classmethod
    def get_driver_class(cls):
        return PyDriverTree

    @classmethod
    def get_parser(cls):
        return PythonParser()

    @classmethod
    def get_resolver(cls):
        return PythonResolver()  # pass tree as arg! just take class TODO!
