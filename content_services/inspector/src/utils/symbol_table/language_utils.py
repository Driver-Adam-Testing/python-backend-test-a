from pathlib import Path

from .base import LanguageProvider
from .providers.c_cpp_provider import CCppLanguageProvider
from .providers.java_provider import JavaLanguageProvider
from .providers.python_provider import PythonLanguageProvider


def get_language_providers() -> dict[str, LanguageProvider]:
    return {
        "python": PythonLanguageProvider(),
        "c_cpp": CCppLanguageProvider(),
        "java": JavaLanguageProvider(),
    }


def detect_language(file_path: Path) -> str | None:
    suffix = file_path.suffix.lower()
    if suffix in {".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".hxx"}:
        return "c_cpp"
    elif suffix == ".py":
        return "python"
    elif suffix == ".java":
        return "java"

    return None


def get_supported_languages() -> list[str]:
    return list(get_language_providers().keys())
