from shared.inspector.utils.lang_specialization.assembly import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT,
    AssemblyDataStructureCollection,
    AssemblyDataStructureRawSymbolCollection,
    AssemblyMacroCollection,
    AssemblyMacroRawSymbolCollection,
    AssemblySubroutineCollection,
    AssemblySubroutineRawSymbolCollection,
    AssemblyVariableCollection,
    AssemblyVariableRawSymbolCollection,
)
from shared.inspector.utils.lang_specialization.default import default_imports_checker
from shared.inspector.utils.templates import S

SOURCE_CODE_LARGE_TEMPLATE_ASSEMBLY = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_SYSTEM_PROMPT_GENERAL_DEFAULT,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    ),
    (
        S.LLM_COND_JSON,
        "# Imports and Dependencies",
        default_imports_checker,
        lambda _llm, output, _code: output,
        None,
    ),
    (
        S.LLM_COND_JSON,
        "# Global Variables",
        AssemblyVariableRawSymbolCollection.from_llm,
        AssemblyVariableCollection.from_llm,
        None,
    ),
    (
        S.LLM_COND_JSON,
        "# Data Structures",
        AssemblyDataStructureRawSymbolCollection.from_llm,
        AssemblyDataStructureCollection.from_llm,
        None,
    ),
    (
        S.LLM_COND_JSON,
        "# Subroutines",
        AssemblySubroutineRawSymbolCollection.from_llm,
        AssemblySubroutineCollection.from_llm,
        None,
    ),
    (
        S.LLM_COND_JSON,
        "# Macros",
        AssemblyMacroRawSymbolCollection.from_llm,
        AssemblyMacroCollection.from_llm,
        None,
    ),
]
