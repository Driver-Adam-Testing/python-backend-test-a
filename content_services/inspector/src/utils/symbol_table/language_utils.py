from .base import LanguageProvider
from .providers.c_cpp_provider import CCppLanguageProvider
from .providers.csharp_provider import CSharpLanguageProvider
from .providers.go_provider import GoLanguageProvider
from .providers.java_provider import JavaLanguageProvider
from .providers.js_ts_provider import JsTsLanguageProvider
from .providers.python_provider import PythonLanguageProvider
from .providers.ruby_provider import RubyLanguageProvider


def get_language_providers() -> dict[str, LanguageProvider]:
    return {
        "python": PythonLanguageProvider(),
        "c_cpp": CCppLanguageProvider(),
        "java": JavaLanguageProvider(),
        "csharp": CSharpLanguageProvider(),
        "js_ts": JsTsLanguageProvider(),
        "go": GoLanguageProvider(),
        "ruby": RubyLanguageProvider(),
    }


def get_supported_languages() -> list[str]:
    return list(get_language_providers().keys())
