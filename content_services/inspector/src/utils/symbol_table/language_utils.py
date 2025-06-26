from .base import LanguageProvider
from .providers.c_cpp_provider import CCppLanguageProvider
from .providers.csharp_provider import CSharpLanguageProvider
from .providers.java_provider import JavaLanguageProvider
from .providers.python_provider import PythonLanguageProvider


def get_language_providers() -> dict[str, LanguageProvider]:
    return {
        "python": PythonLanguageProvider(),
        "c_cpp": CCppLanguageProvider(),
        "java": JavaLanguageProvider(),
        "csharp": CSharpLanguageProvider(),
    }


def get_supported_languages() -> list[str]:
    return list(get_language_providers().keys())
