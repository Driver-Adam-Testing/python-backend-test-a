from utils.lang_specialization.default_multi_context import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
    SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    default_imports_checker_multi_prompt,
)
from utils.lang_specialization.ruby import (
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_RUBY,
    RubyClassRawSymbolCollection,
    RubyModuleRawSymbolCollection,
    class_dict_from_llm_ruby,
    module_dict_from_llm_ruby,
)
from utils.templates import S

SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_RUBY = [
    (
        S.MULTI_PROMPT_TEXT,
        "# Purpose",
        SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_RUBY,
        SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT_MULTI_CONTEXT,
        SOURCE_CODE_PURPOSE_FROM_CHUNKS,
    ),
    (
        S.MULTI_LLM_COND_JSON,
        "# Imports and Dependencies",
        default_imports_checker_multi_prompt,
        lambda _llm, output, _code: output,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Modules",
        RubyModuleRawSymbolCollection.from_static_analysis,
        module_dict_from_llm_ruby,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Classes",
        RubyClassRawSymbolCollection.from_static_analysis,
        class_dict_from_llm_ruby,
        None,
    ),
]
