from shared.prompts.structured_prompting import (
    GENERAL_STE_STYLE_INSTRUCTION,
    NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_CODE_PURPOSE,
    USE_BACKTICKS_STYLE_INSTRUCTION,
    Component,
    Prompt,
)
from utils.lang_specialization.ruby import (
    SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT,
    SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_RUBY,
    RubyClassCollection,
    RubyClassRawSymbolCollection,
    RubyImportRawSymbolCollection,
    RubyMethodCollection,
    RubyModuleCollection,
    RubyModuleRawSymbolCollection,
    RubyTopLevelConstantCollection,
    RubyTopLevelConstantRawSymbolCollection,
    RubyTopLevelMethodRawSymbolCollection,
    RubyTopLevelVariableCollection,
    RubyTopLevelVariableRawSymbolCollection,
    render_ruby_imports,
)
from utils.templates import S

SOURCE_CODE_LARGE_TEMPLATE_RUBY = [
    (
        S.SINGLE_PROMPT_TEXT,
        "# Purpose",
        Prompt.empty()
        .append(Component(string=SOURCE_CODE_LARGE_SYSTEM_PROMPT_GENERAL_RUBY))
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .append(USE_BACKTICKS_STYLE_INSTRUCTION)
        .into_str(),
        Prompt.empty()
        .append(Component(string=SOURCE_CODE_LARGE_PURPOSE_USER_PROMPT))
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_CODE_PURPOSE)
        .into_str(),
    ),
    (
        S.FN_COND_JSON,
        "# Imports and Dependencies",
        RubyImportRawSymbolCollection.from_static_analysis,
        lambda _llm, output, _code: render_ruby_imports(output),
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Global Constants",
        RubyTopLevelConstantRawSymbolCollection.from_static_analysis,
        RubyTopLevelConstantCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Global Variables",
        RubyTopLevelVariableRawSymbolCollection.from_static_analysis,
        RubyTopLevelVariableCollection.from_llm,
        None,
    ),
    (
        S.FN_COND_JSON,
        "# Top Level Methods",
        RubyTopLevelMethodRawSymbolCollection.from_static_analysis,
        RubyMethodCollection.from_llm,
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
