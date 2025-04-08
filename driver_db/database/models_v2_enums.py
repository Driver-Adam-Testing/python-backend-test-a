import enum

import strawberry


class PrimaryAssetKind(str, enum.Enum):
    CODEBASE = "CODEBASE"
    FILE = "FILE"
    PAGE = "PAGE"
    PAGE_TEMPLATE = "PAGE_TEMPLATE"


class VersionStatus(str, enum.Enum):
    GENERATING = "GENERATING"
    GENERATION_COMPLETE = "GENERATION_COMPLETE"
    GENERATION_ERROR = "GENERATION_ERROR"
    CONNECTED = "CONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTION_FAILED = "CONNECTION_FAILED"


class NodeKind(str, enum.Enum):
    CODEBASE_FILE = "CODEBASE_FILE"
    CODEBASE_DIRECTORY = "CODEBASE_DIRECTORY"
    OTHER = "OTHER"


class AutoDocStatusMessageKind(str, enum.Enum):
    RETRIEVING_SOURCES = "RETRIEVING_SOURCES"
    EVALUATING_SECTIONS = "EVALUATING_SECTIONS"
    EVALUATING_SOURCES = "EVALUATING_SOURCES"
    GENERATING_SECTION_DRAFTS = "GENERATING_SECTION_DRAFTS"
    OPTIMIZING_SECTION_STRUCTURE = "OPTIMIZING_CONTENT_STRUCTURE"
    ASSEMBLING_FINAL_DOCUMENT = "ASSEMBLING_FINAL_DOCUMENT"
    COPY_EDITING = "COPY_EDITING"
    GENERATION_COMPLETE = "GENERATION_COMPLETE"
    GENERATION_ERROR = "GENERATION_ERROR"


@strawberry.enum
class ContentKind(str, enum.Enum):
    PDF_VISUAL_SUMMARY = "pdf-visual-summary"
    PDF_TEXT_SUMMARY = "pdf-text-summary"
    PDF_IMAGE_SUMMARY = "pdf-image-summary"
    PDF_EXTRACTED_TEXT = "pdf-extracted-text"
    PDF_EXTRACTED_TABLE = "pdf-extracted-table"
    TEMPLATE = "template"
    SHORT_PARAGRAPH_DESCRIPTION = "short_paragraph_description"
    TERSE_SENTENCE_DESCRIPTION = "terse_sentence_description"
    LONG_DESCRIPTION = "long_description"
    QUICK_START_ENTRY = "quick_start_entry"
    QUICK_START_GETTING_STARTED = "quick_start_getting_started"
    QUICK_START_DEPENDENCIES = "quick_start_dependencies"
    QUICK_START_USE = "quick_start_use"
    ARCHITECTURE_DIAGRAM = "architecture_diagram"
    CHUNK_DESCRIPTIONS = "chunk_descriptions"
    application_note = "application_note"
    SHORT_SENTENCE_DESCRIPTION = "short_sentence_description"
    SYMBOL = "symbol"
    PDF_SUMMARY = "pdf_summary"
    CODEBASE = "codebase"
    CODEBASE_DIRECTORY = "codebase-directory"
    CODEBASE_FILE = "codebase-file"
    SUPPLEMENTAL_DOCUMENT = "supplemental-document"
    TOP_LEVEL_SHORT_SENTENCE = "TOP_LEVEL_SHORT_SENTENCE"
    TOP_LEVEL_SHORT_PARAGRAPH = "TOP_LEVEL_SHORT_PARAGRAPH"
    TOP_LEVEL_TERSE_SENTENCE = "TOP_LEVEL_TERSE_SENTENCE"
    TOP_LEVEL_LONG_DESCRIPTION = "TOP_LEVEL_LONG_DESCRIPTION"


class FileTypeEnum(enum.Enum):
    PYTHON = "PYTHON"
    GROOVY = "GROOVY"
    C = "C"
    HEADER = "HEADER"
    CPP = "CPP"
    ASSEMBLY = "ASSEMBLY"
    LINKER_SCRIPT = "LINKER_SCRIPT"
    ACTIONSCRIPT = "ACTIONSCRIPT"
    HPP = "HPP"
    JAVA = "JAVA"
    JAVASCRIPT = "JAVASCRIPT"
    TYPESCRIPT = "TYPESCRIPT"
    GO = "GO"
    RUST = "RUST"
    SHELL = "SHELL"
    BATCH = "BATCH"
    TEMPLATE = "TEMPLATE"
    DART = "DART"
    KOTLIN = "KOTLIN"
    SWIFT = "SWIFT"
    CXX = "CXX"
    OBJECTIVE_C = "OBJECTIVE_C"
    VERILOG = "VERILOG"
    SYSTEM_VERILOG = "SYSTEM_VERILOG"
    VHDL = "VHDL"
    CSHARP = "CSHARP"
    TERRAFORM = "TERRAFORM"
    SQL = "SQL"
    SAS = "SAS"
    RUBY = "RUBY"
    PERL = "PERL"
    COBOL = "COBOL"
    D = "D"
    NSIS = "NSIS"
    SCSS = "SCSS"
    LESS = "LESS"
    HTML = "HTML"
    CSS = "CSS"
    CRYSTAL = "CRYSTAL"
    TCL = "TCL"
    JSON = "JSON"
    YAML = "YAML"
    TOML = "TOML"
    MARKDOWN = "MARKDOWN"
    TEXT = "TEXT"
    RESTRUCTUREDTEXT = "RESTRUCTUREDTEXT"
    XML = "XML"
    JSX = "JSX"
    INI = "INI"
    CONFIG = "CONFIG"
    DITA = "DITA"
    ADOC = "ADOC"
    ASPX = "ASPX"
    CMX = "CMX"
    PEP = "PEP"
    APP = "APP"
    PRE = "PRE"
    LST = "LST"
    DRIVER_PAGE = "DRIVER_PAGE"
    UNKNOWN = "UNKNOWN"


def get_file_type(extension: str) -> FileTypeEnum:
    extension_map = {
        ".py": FileTypeEnum.PYTHON,
        ".groovy": FileTypeEnum.GROOVY,
        ".c": FileTypeEnum.C,
        ".h": FileTypeEnum.HEADER,
        ".cpp": FileTypeEnum.CPP,
        ".s": FileTypeEnum.ASSEMBLY,
        ".S": FileTypeEnum.ASSEMBLY,
        ".ld": FileTypeEnum.LINKER_SCRIPT,
        ".sct": FileTypeEnum.LINKER_SCRIPT,
        ".icf": FileTypeEnum.LINKER_SCRIPT,
        ".as": FileTypeEnum.ACTIONSCRIPT,
        ".asm": FileTypeEnum.ASSEMBLY,
        ".hpp": FileTypeEnum.HPP,
        ".java": FileTypeEnum.JAVA,
        ".js": FileTypeEnum.JAVASCRIPT,
        ".ts": FileTypeEnum.TYPESCRIPT,
        ".tsx": FileTypeEnum.TYPESCRIPT,
        ".go": FileTypeEnum.GO,
        ".rs": FileTypeEnum.RUST,
        ".sh": FileTypeEnum.SHELL,
        ".bat": FileTypeEnum.BATCH,
        ".tpl": FileTypeEnum.TEMPLATE,
        ".inc": FileTypeEnum.TEMPLATE,
        ".dart": FileTypeEnum.DART,
        ".kt": FileTypeEnum.KOTLIN,
        ".kts": FileTypeEnum.KOTLIN,
        ".swift": FileTypeEnum.SWIFT,
        ".cxx": FileTypeEnum.CXX,
        ".m": FileTypeEnum.OBJECTIVE_C,
        ".v": FileTypeEnum.VERILOG,
        ".sv": FileTypeEnum.SYSTEM_VERILOG,
        ".vhd": FileTypeEnum.VHDL,
        ".cs": FileTypeEnum.CSHARP,
        ".tf": FileTypeEnum.TERRAFORM,
        ".tfvars": FileTypeEnum.TERRAFORM,
        ".sql": FileTypeEnum.SQL,
        ".sas": FileTypeEnum.SAS,
        ".rb": FileTypeEnum.RUBY,
        ".pl": FileTypeEnum.PERL,
        ".cbl": FileTypeEnum.COBOL,
        ".cob": FileTypeEnum.COBOL,
        ".d": FileTypeEnum.D,
        ".nsi": FileTypeEnum.NSIS,
        ".scss": FileTypeEnum.SCSS,
        ".less": FileTypeEnum.LESS,
        ".html": FileTypeEnum.HTML,
        ".css": FileTypeEnum.CSS,
        ".cr": FileTypeEnum.CRYSTAL,
        ".tcl": FileTypeEnum.TCL,
        ".tcb": FileTypeEnum.TCL,
        ".json": FileTypeEnum.JSON,
        ".yml": FileTypeEnum.YAML,
        ".yaml": FileTypeEnum.YAML,
        ".toml": FileTypeEnum.TOML,
        ".md": FileTypeEnum.MARKDOWN,
        ".mkd": FileTypeEnum.MARKDOWN,
        ".mk": FileTypeEnum.MARKDOWN,
        ".txt": FileTypeEnum.TEXT,
        ".rst": FileTypeEnum.RESTRUCTUREDTEXT,
        ".xml": FileTypeEnum.XML,
        ".jsx": FileTypeEnum.JSX,
        ".ini": FileTypeEnum.INI,
        ".conf": FileTypeEnum.CONFIG,
        ".dita": FileTypeEnum.DITA,
        ".ditamap": FileTypeEnum.DITA,
        ".adoc": FileTypeEnum.ADOC,
        ".tt": FileTypeEnum.TEMPLATE,
        ".config": FileTypeEnum.CONFIG,
        ".settings": FileTypeEnum.CONFIG,
        ".aspx": FileTypeEnum.ASPX,
        ".cmx": FileTypeEnum.CMX,
        ".pep": FileTypeEnum.PEP,
        ".app": FileTypeEnum.APP,
        ".pre": FileTypeEnum.PRE,
        ".lst": FileTypeEnum.LST,
        ".driver_page": FileTypeEnum.DRIVER_PAGE,
    }
    return extension_map.get(extension, FileTypeEnum.UNKNOWN)


class LlmPipelineKind(str, enum.Enum):
    DEFAULT = "DEFAULT"
    CHAT = "CHAT"
    PAGE_CONTEXT_ABBREVIATION = "PAGE_CONTEXT_ABBREVIATION"
    SMART_INSTRUCTION_MAIN_LOOP = "SMART_INSTRUCTION_MAIN_LOOP"
