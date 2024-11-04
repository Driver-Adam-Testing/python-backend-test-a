from utils.lang_specialization.default import (
    default_imports_checker,
)
from utils.lang_specialization.ruby import (
    SOURCE_CODE_SMALL_PURPOSE_USER_PROMPT,
    SOURCE_CODE_SMALL_SYSTEM_PROMPT_GENERAL_RUBY,
    RubyClassRawSymbolCollection,
    RubyModuleRawSymbolCollection,
    class_dict_from_llm_ruby,
    module_dict_from_llm_ruby,
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
