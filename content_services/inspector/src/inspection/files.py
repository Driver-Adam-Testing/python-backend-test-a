import logging
from enum import IntEnum
from pathlib import Path
from typing import Any, Self

import modal
import openai
from pydantic import BaseModel, ValidationError
from utils.dag import LiteNode
from utils.io import (
    get_prompt_template,
)
from utils.lang_specialization.symbol_common import Lang, disambiguate_header
from utils.models import ChatOpenAI
from utils.templates import Template

from inspection.prompt_templates.files.templates.metadata_large_default import (
    METADATA_LARGE_TEMPLATE,
)
from inspection.prompt_templates.files.templates.metadata_medium_default import (
    METADATA_MEDIUM_TEMPLATE,
)
from inspection.prompt_templates.files.templates.metadata_multi_context_default import (
    METADATA_MULTI_CONTEXT_TEMPLATE,
)
from inspection.prompt_templates.files.templates.metadata_small_default import (
    METADATA_SMALL_TEMPLATE,
)
from inspection.prompt_templates.files.templates.source_code_large_assembly import (
    SOURCE_CODE_LARGE_TEMPLATE_ASSEMBLY,
)
from inspection.prompt_templates.files.templates.source_code_large_assembly_multi_prompt import (
    SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_ASSEMBLY,
)
from inspection.prompt_templates.files.templates.source_code_large_c import (
    SOURCE_CODE_LARGE_TEMPLATE_C,
)
from inspection.prompt_templates.files.templates.source_code_large_c_multi_prompt import (
    SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_C,
)
from inspection.prompt_templates.files.templates.source_code_large_cpp import (
    SOURCE_CODE_LARGE_TEMPLATE_CPP,
)
from inspection.prompt_templates.files.templates.source_code_large_cpp_multi_prompt import (
    SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_CPP,
)
from inspection.prompt_templates.files.templates.source_code_large_cs import (
    SOURCE_CODE_LARGE_TEMPLATE_CS,
)
from inspection.prompt_templates.files.templates.source_code_large_cs_multi_prompt import (
    SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_CS,
)
from inspection.prompt_templates.files.templates.source_code_large_default import (
    SOURCE_CODE_LARGE_TEMPLATE_DEFAULT,
)
from inspection.prompt_templates.files.templates.source_code_large_header import (
    SOURCE_CODE_LARGE_TEMPLATE_HEADER,
)
from inspection.prompt_templates.files.templates.source_code_large_header_multi_prompt import (
    SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_HEADER,
)
from inspection.prompt_templates.files.templates.source_code_large_java import (
    SOURCE_CODE_LARGE_TEMPLATE_JAVA,
)
from inspection.prompt_templates.files.templates.source_code_large_java_multi_prompt import (
    SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_JAVA,
)
from inspection.prompt_templates.files.templates.source_code_large_py import (
    SOURCE_CODE_LARGE_TEMPLATE_PY,
)
from inspection.prompt_templates.files.templates.source_code_large_py_multi_prompt import (
    SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_PY,
)
from inspection.prompt_templates.files.templates.source_code_large_ruby import (
    SOURCE_CODE_LARGE_TEMPLATE_RUBY,
)
from inspection.prompt_templates.files.templates.source_code_large_ruby_multi_prompt import (
    SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_RUBY,
)
from inspection.prompt_templates.files.templates.source_code_large_rust import (
    SOURCE_CODE_LARGE_TEMPLATE_RUST,
)
from inspection.prompt_templates.files.templates.source_code_large_rust_multi_prompt import (
    SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_RUST,
)
from inspection.prompt_templates.files.templates.source_code_large_verilog import (
    SOURCE_CODE_LARGE_TEMPLATE_VERILOG,
)
from inspection.prompt_templates.files.templates.source_code_large_verilog_multi_prompt import (
    SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_VERILOG,
)
from inspection.prompt_templates.files.templates.source_code_multi_context_default import (
    SOURCE_CODE_MULTI_CONTEXT_TEMPLATE_DEFAULT,
)
from inspection.prompt_templates.files.templates.source_code_small_assembly import (
    SOURCE_CODE_SMALL_TEMPLATE_ASSEMBLY,
)
from inspection.prompt_templates.files.templates.source_code_small_c import (
    SOURCE_CODE_SMALL_TEMPLATE_C,
)
from inspection.prompt_templates.files.templates.source_code_small_cpp import (
    SOURCE_CODE_SMALL_TEMPLATE_CPP,
)
from inspection.prompt_templates.files.templates.source_code_small_cs import (
    SOURCE_CODE_SMALL_TEMPLATE_CS,
)
from inspection.prompt_templates.files.templates.source_code_small_default import (
    SOURCE_CODE_SMALL_TEMPLATE_DEFAULT,
)
from inspection.prompt_templates.files.templates.source_code_small_header import (
    SOURCE_CODE_SMALL_TEMPLATE_HEADER,
)
from inspection.prompt_templates.files.templates.source_code_small_java import (
    SOURCE_CODE_SMALL_TEMPLATE_JAVA,
)
from inspection.prompt_templates.files.templates.source_code_small_py import (
    SOURCE_CODE_SMALL_TEMPLATE_PY,
)
from inspection.prompt_templates.files.templates.source_code_small_ruby import (
    SOURCE_CODE_SMALL_TEMPLATE_RUBY,
)
from inspection.prompt_templates.files.templates.source_code_small_rust import (
    SOURCE_CODE_SMALL_TEMPLATE_RUST,
)
from inspection.prompt_templates.files.templates.source_code_small_verilog import (
    SOURCE_CODE_SMALL_TEMPLATE_VERILOG,
)

PARENT_PATH = Path(__file__).parent


SMALL_METADATA_FILE_CUTOFF_BYTES = 500
MEDIUM_METADATA_FILE_CUTOFF_BYTES = 2500


class _FileEnumLLM(IntEnum):
    SOURCE_CODE_LARGE = 0
    SOURCE_CODE_SMALL = 1
    METADATA = 2


class _FileKindLLM(BaseModel):
    kind: _FileEnumLLM


class FileEnum(IntEnum):
    SOURCE_CODE_LARGE = 0
    SOURCE_CODE_SMALL = 1
    METADATA_LARGE = 2
    METADATA_MEDIUM = 3
    METADATA_SMALL = 4


class FileKind(BaseModel):
    kind: FileEnum

    @classmethod
    def _from_file_kind_llm(cls, code: str, fk_llm: _FileKindLLM) -> Self:
        match fk_llm.kind:
            case _FileEnumLLM.METADATA:
                num_bytes = len(code.encode("utf-8"))
                if num_bytes <= SMALL_METADATA_FILE_CUTOFF_BYTES:
                    return cls(kind=FileEnum.METADATA_SMALL)
                elif num_bytes <= MEDIUM_METADATA_FILE_CUTOFF_BYTES:
                    return cls(kind=FileEnum.METADATA_MEDIUM)
                else:
                    return cls(kind=FileEnum.METADATA_LARGE)
            case _FileEnumLLM.SOURCE_CODE_LARGE:
                return cls(kind=FileEnum.SOURCE_CODE_LARGE)
            case _FileEnumLLM.SOURCE_CODE_SMALL:
                return cls(kind=FileEnum.SOURCE_CODE_SMALL)
            case _:
                raise ValueError("Unreachable")

    @classmethod
    def from_llm(
        cls,
        llm: ChatOpenAI,
        file_name: str,
        code: str,
        fallback_kind: FileEnum = FileEnum.SOURCE_CODE_LARGE,
    ) -> Self:
        system_prompt = get_prompt_template(
            PARENT_PATH / "prompt_templates/files/determine_file_kind.txt"
        )
        human_prompt = ""
        human_prompt += f"File name: {file_name}\n\nFile contents:\n\n{code}"
        file_kind_raw = llm.generate_response(system_prompt, human_prompt)
        try:
            file_kind_from_llm = _FileKindLLM(kind=int(file_kind_raw))
            file_kind = cls._from_file_kind_llm(code=code, fk_llm=file_kind_from_llm)
        except ValueError as e:
            logging.warn(
                f"Failed to parse integer from LLM response to determine file kind for file {file_name}: {e}"
            )
            file_kind = cls(kind=fallback_kind)
        except ValidationError as e:
            logging.warn(
                f"Invalid integer enum variant parsed from LLM to determine file kind for file {file_name}: {e}"
            )
            file_kind = cls(kind=fallback_kind)

        return file_kind


SOURCE_CODE_LARGE_BY_LANG = {
    Lang.DEFAULT: SOURCE_CODE_LARGE_TEMPLATE_DEFAULT,
    Lang.C: SOURCE_CODE_LARGE_TEMPLATE_C,
    Lang.CPP: SOURCE_CODE_LARGE_TEMPLATE_CPP,
    Lang.C_OR_CPP_HEADER: SOURCE_CODE_LARGE_TEMPLATE_HEADER,
    Lang.PYTHON: SOURCE_CODE_LARGE_TEMPLATE_PY,
    Lang.VERILOG: SOURCE_CODE_LARGE_TEMPLATE_VERILOG,
    Lang.RUST: SOURCE_CODE_LARGE_TEMPLATE_RUST,
    Lang.ASSEMBLY: SOURCE_CODE_LARGE_TEMPLATE_ASSEMBLY,
    Lang.JAVA: SOURCE_CODE_LARGE_TEMPLATE_JAVA,
    Lang.RUBY: SOURCE_CODE_LARGE_TEMPLATE_RUBY,
    Lang.C_SHARP: SOURCE_CODE_LARGE_TEMPLATE_CS,
}
SOURCE_CODE_SMALL_BY_LANG = {
    Lang.DEFAULT: SOURCE_CODE_SMALL_TEMPLATE_DEFAULT,
    Lang.C: SOURCE_CODE_SMALL_TEMPLATE_C,
    Lang.CPP: SOURCE_CODE_SMALL_TEMPLATE_CPP,
    Lang.C_OR_CPP_HEADER: SOURCE_CODE_SMALL_TEMPLATE_HEADER,
    Lang.PYTHON: SOURCE_CODE_SMALL_TEMPLATE_PY,
    Lang.VERILOG: SOURCE_CODE_SMALL_TEMPLATE_VERILOG,
    Lang.RUST: SOURCE_CODE_SMALL_TEMPLATE_RUST,
    Lang.ASSEMBLY: SOURCE_CODE_SMALL_TEMPLATE_ASSEMBLY,
    Lang.JAVA: SOURCE_CODE_SMALL_TEMPLATE_JAVA,
    Lang.RUBY: SOURCE_CODE_SMALL_TEMPLATE_RUBY,
    Lang.C_SHARP: SOURCE_CODE_SMALL_TEMPLATE_CS,
}
METADATA_SMALL_BY_LANG = {
    Lang.DEFAULT: METADATA_SMALL_TEMPLATE,
    Lang.C: METADATA_SMALL_TEMPLATE,
    Lang.CPP: METADATA_SMALL_TEMPLATE,
    Lang.C_OR_CPP_HEADER: METADATA_SMALL_TEMPLATE,
    Lang.PYTHON: METADATA_SMALL_TEMPLATE,
    Lang.VERILOG: METADATA_SMALL_TEMPLATE,
    Lang.RUST: METADATA_SMALL_TEMPLATE,
    Lang.ASSEMBLY: METADATA_SMALL_TEMPLATE,
    Lang.JAVA: METADATA_SMALL_TEMPLATE,
    Lang.RUBY: METADATA_SMALL_TEMPLATE,
    Lang.C_SHARP: METADATA_SMALL_TEMPLATE,
}
METADATA_MEDIUM_BY_LANG = {
    Lang.DEFAULT: METADATA_MEDIUM_TEMPLATE,
    Lang.C: METADATA_MEDIUM_TEMPLATE,
    Lang.CPP: METADATA_MEDIUM_TEMPLATE,
    Lang.C_OR_CPP_HEADER: METADATA_MEDIUM_TEMPLATE,
    Lang.PYTHON: METADATA_MEDIUM_TEMPLATE,
    Lang.VERILOG: METADATA_MEDIUM_TEMPLATE,
    Lang.RUST: METADATA_MEDIUM_TEMPLATE,
    Lang.ASSEMBLY: METADATA_MEDIUM_TEMPLATE,
    Lang.JAVA: METADATA_MEDIUM_TEMPLATE,
    Lang.RUBY: METADATA_MEDIUM_TEMPLATE,
    Lang.C_SHARP: METADATA_MEDIUM_TEMPLATE,
}
METADATA_LARGE_BY_LANG = {
    Lang.DEFAULT: METADATA_LARGE_TEMPLATE,
    Lang.C: METADATA_LARGE_TEMPLATE,
    Lang.CPP: METADATA_LARGE_TEMPLATE,
    Lang.C_OR_CPP_HEADER: METADATA_LARGE_TEMPLATE,
    Lang.PYTHON: METADATA_LARGE_TEMPLATE,
    Lang.VERILOG: METADATA_LARGE_TEMPLATE,
    Lang.RUST: METADATA_LARGE_TEMPLATE,
    Lang.ASSEMBLY: METADATA_LARGE_TEMPLATE,
    Lang.JAVA: METADATA_LARGE_TEMPLATE,
    Lang.RUBY: METADATA_LARGE_TEMPLATE,
    Lang.C_SHARP: METADATA_LARGE_TEMPLATE,
}
TEMPLATE_DATA = {
    FileEnum.SOURCE_CODE_LARGE: SOURCE_CODE_LARGE_BY_LANG,
    FileEnum.SOURCE_CODE_SMALL: SOURCE_CODE_SMALL_BY_LANG,
    FileEnum.METADATA_LARGE: METADATA_LARGE_BY_LANG,
    FileEnum.METADATA_MEDIUM: METADATA_MEDIUM_BY_LANG,
    FileEnum.METADATA_SMALL: METADATA_SMALL_BY_LANG,
}


def file_long_from_code(
    llm: ChatOpenAI, file_name: str, codebase_name: str, path: str | Path, code: str
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH / "prompt_templates/files/long_from_code.txt"
    )
    human_prompt = (
        f"`{file_name}` in codebase `{codebase_name}` with path `{path!s}`:\n\n{code}"
    )
    return llm.generate_response(system_prompt, human_prompt)


def file_single_sentence_from_chunk_descriptions(
    llm: ChatOpenAI, chunks: list[str], file_name: str, codebase_name: str
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/files/single_sentence_from_chunk_descriptions.txt"
    )
    human_prompt = ""
    for idx, chunk in enumerate(chunks, start=1):
        human_prompt += f"\n\nDescription of piece {idx} in `{file_name} of codebase {codebase_name}:\n\n{chunk}"
    return llm.generate_response(system_prompt, human_prompt)


def file_single_paragraph_from_chunk_descriptions(
    llm: ChatOpenAI, chunks: list[str], file_name: str, codebase_name: str
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/files/single_paragraph_from_chunk_descriptions.txt"
    )
    human_prompt = ""
    for idx, chunk in enumerate(chunks, start=1):
        human_prompt += f"\n\nDescription of piece {idx} in `{file_name} of codebase {codebase_name}:\n\n{chunk}"
    return llm.generate_response(system_prompt, human_prompt)


def file_long_from_chunk_descriptions(
    llm: ChatOpenAI,
    chunks: list[str],
    file_name: str,
    codebase_name: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH / "prompt_templates/files/long_from_chunk_descriptions.txt"
    )
    human_prompt = ""
    for idx, chunk in enumerate(chunks, start=1):
        human_prompt += f"\n\nDescription of piece {idx} in `{file_name} of codebase {codebase_name}:\n\n{chunk}\n\n"
    return llm.generate_response(system_prompt, human_prompt)


def file_compress_chunks(
    llm: ChatOpenAI,
    file_name: str,
    description_chunk: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH / "prompt_templates/files/compress_chunks.txt"
    )
    human_prompt = f"Chunk of file chunk descriptions for file `{file_name}`:\n\n{description_chunk}"
    return llm.generate_response(system_prompt, human_prompt)


def file_chunk_description(
    llm: ChatOpenAI,
    file_name: str | Path,
    codebase_name: str,
    path: str | Path,
    code_chunk: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH / "prompt_templates/files/chunk_description.txt"
    )
    human_prompt = f"Piece of code from `{file_name}` in codebase `{codebase_name}` with path `{path}`:\n\n{code_chunk}"
    return llm.generate_response(system_prompt, human_prompt)


def file_single_sentence_from_code(
    llm: ChatOpenAI,
    file_name: str | Path,
    codebase_name: str,
    path: str | Path,
    code: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH / "prompt_templates/files/single_sentence_from_code.txt"
    )
    human_prompt = (
        f"`{file_name}` in codebase `{codebase_name}` with path `{path}`:\n\n{code}"
    )
    return llm.generate_response(system_prompt, human_prompt)


def file_single_paragraph_from_code(
    llm: ChatOpenAI, file_name: str, codebase_name: str, path: str | Path, code: str
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH / "prompt_templates/files/single_paragraph_from_code.txt"
    )
    human_prompt = (
        f"`{file_name}` in codebase `{codebase_name}` with path `{path}`:\n\n{code}"
    )
    return llm.generate_response(system_prompt, human_prompt)


def _return_with_simple_message(message: str) -> dict[str, Any]:
    return {
        "chunk_descriptions": message,
        "short": {
            "single_sentence": message,
            "single_paragraph": message,
        },
        "long": message,
        "architecture": "",
    }


# TODO: address C901
def comprehend_file_top_down(
    llm: ChatOpenAI,
    node: LiteNode,
    source_code: str,
    codebase_name: str,
    chunk_size: int,
    chunk_overlap: int,
    compression_loop_max_itr: int,
    max_num_chunks: int,
    raise_hard_errors: bool = True,
) -> tuple[bool, dict[str, Any]]:
    from shared.chunking.text_splitter import split_text

    logging.info(f"Incorporating `{node.root_rel_path}`")

    if len(source_code.strip()) == 0:
        description = "Empty file (no analyzable contents)."
        success = False
        results = _return_with_simple_message(
            message=description,
        )
        return success, results

    chunks = split_text(
        text=source_code, chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    if len(chunks) > max_num_chunks:
        if raise_hard_errors:
            raise ValueError(
                f"File `{node.root_rel_path}` too large to process: {len(chunks)} chunks greater than max of {max_num_chunks} chunks."
            )
        else:
            logging.warning(
                f"File `{node.root_rel_path}` too large to process: {len(chunks)} chunks greater than max of {max_num_chunks} chunks."
            )
            print(
                f"WARNING: File `{node.root_rel_path}` too large to process: {len(chunks)} chunks greater than max of {max_num_chunks} chunks."
            )
            description = "File too large to process."
            success = False
            results = _return_with_simple_message(
                message=description,
            )
            return (success, results)
    if len(chunks) > 1:
        chunk_texts = [c.text for c in chunks]

        logging.info(f"Processing {len(chunks)} chunks for `{node.root_rel_path}`")
        print(f"Processing {len(chunks)} chunks for `{node.root_rel_path}` ...")
        try:
            file_kind = FileKind.from_llm(
                llm=llm, file_name=node.root_rel_path.name, code=chunk_texts[0]
            )

            match file_kind.kind:
                case (
                    FileEnum.METADATA_SMALL
                    | FileEnum.METADATA_MEDIUM
                    | FileEnum.METADATA_LARGE
                ):
                    template = METADATA_MULTI_CONTEXT_TEMPLATE
                    long_template = Template(template=template)
                    file_description_long = long_template.run_with_code(
                        llm=llm,
                        root_rel_path=node.root_rel_path,
                        code=source_code,
                        code_chunks=chunk_texts,
                    )
                case _:
                    language = Lang.from_ext_and_source(
                        ext=node.root_rel_path.suffix, source=chunk_texts[0]
                    )

                    if language == Lang.C_OR_CPP_HEADER:
                        language = disambiguate_header(
                            code=chunk_texts[0], fallback=Lang.C_OR_CPP_HEADER
                        )
                        print(
                            f"Disambiguated header file `{node.root_rel_path}` to be `{language}`"
                        )
                        if language == Lang.CPP:
                            # We still defer to the generic header template if c++, but we use C language specialization
                            # for C headers.
                            language = Lang.C_OR_CPP_HEADER

                    match language:
                        case Lang.C:
                            template = SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_C
                        case Lang.CPP:
                            template = SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_CPP
                        case Lang.C_OR_CPP_HEADER:
                            template = SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_HEADER
                        case Lang.PYTHON:
                            template = SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_PY
                        case Lang.RUST:
                            template = SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_RUST
                        case Lang.JAVA:
                            template = SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_JAVA
                        case Lang.RUBY:
                            template = SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_RUBY
                        case Lang.ASSEMBLY:
                            template = SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_ASSEMBLY
                        case Lang.VERILOG:
                            template = SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_VERILOG
                        case Lang.C_SHARP:
                            template = SOURCE_CODE_LARGE_MULTI_PROMPT_TEMPLATE_CS
                        case _:
                            template = SOURCE_CODE_MULTI_CONTEXT_TEMPLATE_DEFAULT
                    long_template = Template(template=template)
                    file_description_long = long_template.run_with_code(
                        llm=llm,
                        root_rel_path=node.root_rel_path,
                        code=source_code,
                        code_chunks=chunk_texts,
                    )
            # Now ready to generate final documentation content.
            description_chunks = split_text(
                text=file_description_long,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            if len(description_chunks) > 1:
                chunks = [description_chunks[0].text]
            else:
                chunks = [file_description_long]
            chunk_detailed_descriptions = [file_description_long]
            file_description_single_sentence = (
                file_single_sentence_from_chunk_descriptions(
                    llm=llm,
                    chunks=chunks,
                    file_name=node.root_rel_path.name,
                    codebase_name=codebase_name,
                )
            )
            file_description_single_paragraph = (
                file_single_paragraph_from_chunk_descriptions(
                    llm=llm,
                    chunks=chunks,
                    file_name=node.root_rel_path.name,
                    codebase_name=codebase_name,
                )
            )
        except openai.BadRequestError as e:
            email_func = modal.Function.lookup("inspector-v2", "send_exception_email")
            exception_details = f"NON-BREAKING EXCEPTION:\nBadRequestError from OpenAI: {e.message}.\nCheck logs for additional details."
            email_func.remote(exception_details)

            print("BadRequestError processing file: ", e)
            description = "Could not process file"
            success = False
            results = _return_with_simple_message(
                message=description,
            )
            return success, results

    # TODO: Vulnerable to edge case with code map + source code is over the context window length.
    else:
        try:
            # file_description_long = file_long_from_code(
            #     llm=llm,
            #     file_name=node.root_rel_path.name,
            #     codebase_name=codebase_name,
            #     path=node.root_rel_path,
            #     code=source_code,
            # )
            file_kind = FileKind.from_llm(
                llm=llm, file_name=node.root_rel_path.name, code=source_code
            )
            language = Lang.from_ext_and_source(
                ext=node.root_rel_path.suffix, source=source_code
            )
            if language == Lang.C_OR_CPP_HEADER:
                language = disambiguate_header(
                    code=source_code, fallback=Lang.C_OR_CPP_HEADER
                )
                print(
                    f"Disambiguated header file `{node.root_rel_path}` to be `{language}`"
                )
                if language == Lang.CPP:
                    # We still defer to the generic header template if c++, but we use C language specialization
                    # for C headers.
                    language = Lang.C_OR_CPP_HEADER

            template = TEMPLATE_DATA[file_kind.kind][language]
            long_template = Template(template=template)
            file_description_long = long_template.run_with_code(
                llm=llm, root_rel_path=node.root_rel_path, code=source_code
            )
            chunk_detailed_descriptions = [file_description_long]
            file_description_single_sentence = file_single_sentence_from_code(
                llm=llm,
                file_name=node.root_rel_path.name,
                codebase_name=codebase_name,
                path=node.root_rel_path,
                code=source_code,
            )
            file_description_single_paragraph = file_single_paragraph_from_code(
                llm=llm,
                file_name=node.root_rel_path.name,
                codebase_name=codebase_name,
                path=node.root_rel_path,
                code=source_code,
            )
        except openai.BadRequestError as e:
            email_func = modal.Function.lookup("inspector-v2", "send_exception_email")
            exception_details = f"NON-BREAKING EXCEPTION:\nBadRequestError from OpenAI: {e.message}.\nCheck logs for additional details."
            email_func.remote(exception_details)

            # TODO: this is a hack. Should rethink the tokenizing
            print("BadRequestError processing file: ", e)
            description = "Could not process file"
            success = False
            results = _return_with_simple_message(
                message=description,
            )
            return success, results

    short_descriptions = {
        "single_sentence": file_description_single_sentence,
        "single_paragraph": file_description_single_paragraph,
    }
    logging.info(
        f"Short description for `{node.root_rel_path}` at `{codebase_name}`:\n{short_descriptions['single_paragraph']}"
    )

    success = True
    results = {
        "chunk_descriptions": chunk_detailed_descriptions,
        "short": short_descriptions,
        "long": file_description_long,
        "architecture": "",
    }
    return (success, results)
