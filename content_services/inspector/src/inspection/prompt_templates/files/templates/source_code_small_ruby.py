from utils.lang_specialization.default import (
    default_imports_checker,
)
from utils.lang_specialization.ruby import (
    SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
    SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_RUBY,
    RubyClassCollection,
    RubyClassRawSymbolCollection,
    RubyModuleCollection,
    RubyModuleRawSymbolCollection,
)
from utils.templates import S

SOURCE_CODE_SMALL_TEMPLATE_RUBY = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_RUBY,
        SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
    ),
    (
        S.LLM_COND_JSON,
        "# Imports and Dependencies",
        default_imports_checker,
        lambda _llm, output, _code: output,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Modules",
        RubyModuleRawSymbolCollection.from_static_analysis,
        RubyModuleCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Classes",
        RubyClassRawSymbolCollection.from_static_analysis,
        RubyClassCollection.from_llm,
        None,
    ),
]
