import logging
from pathlib import Path
from typing import Any

import openai
from pydantic import BaseModel
from utils.dag import LiteNode
from utils.io import (
    get_prompt_template,
)
from utils.llm import (
    chunk_str,
)
from utils.models import ChatOpenAI

PARENT_PATH = Path(__file__).parent


SIMPLE_START_SYSTEM_PROMPT = """
You are a software engineering documentation expert. You write detailed documentation to explain software.

You are skilled at explaining technical details as well as recognize and articulate the key conceptual components and purpose of software.
"""

PURPOSE_PROMPT = """
In a single paragraph of 3 to 5 sentences, explain the purpose of the code provided below. Answer questions such as:

- Does this code provide a narrow and specific functionality? If so, what is that?
- Is this code a collection of many different components? If so, what is the common them or purpose?
- Is this code clearly an executable script, a library intended to be imported elsewhere, or does it define public APIs?
"""

TECHNICAL_SUMMARY_PROMPT = """
In one or more paragraphs, summarize the technical details of the code provided below. Choose a summary length appropriate for the length and complexity of code. Longer and more complex code should have more summary content.

In writing your technical summary, consider the following:
- What are the most important technical details that a developer working with this could should know.
"""

IMPORTS_PROMPT = """
Summarize the dependencies or imports used in the code provided below.

- If there are none, just say so.
- Do not speculate on the nature of the imports or dependencies if it is not clear what they are for. If it is not clear, just identify the name. If it is clear what an import or dependency is, briefly describe it.
"""

DATA_STRUCTURES_PROMPT = """
Summarize the data structures in the code provided below.

- If there are none, just say so.
- If there are relatively few, describe each of them.
- If there are many, focus on the most important data structures.
- When describing a data structure, provide detail that matches the complexity of the data structure. Large and complex data structures should get longer explanations, while small ones a single sentence.
- Provide your output in a list, where each item of the list is a data structure.
"""

FUNCTIONS_PROMPT = """
Summarize the functions or methods in the code provided below. For each function or method, describe the inputs, control flow and logic, and output.

- If there are none, just say so.
- If there are relatively few, describe each of them.
- If there are many, focus on the most important functions or methods.
- If you are describing a method rather than a free function, identify the class the method is associated with.
- When describing a function or method, provide detail that matches the complexity of the function or method body. Large and complex functions or methods should get longer explanations, while small ones much less.
- Provide your output such that each function or method is described in a 3rd level markdown header where the function or method name is the header title (e.g., ### <function_name>).
"""

DIAGRAMS_PROMPT = """
Build an ASCII diagram that represents the logical flow of the code provided below.
"""

SIMPLE_START_TEMPLATE = [
    ("# Overview",),
    ("## Purpose", PURPOSE_PROMPT),
    ("## Technical Summary", TECHNICAL_SUMMARY_PROMPT),
    ("## Imports and Dependencies", IMPORTS_PROMPT),
    ("## Data Structures", DATA_STRUCTURES_PROMPT),
    ("## Functions", FUNCTIONS_PROMPT),
    # ("## Diagram", DIAGRAMS_PROMPT),
]


class Template(BaseModel):
    system_prompt: str
    template: list[tuple[str] | tuple[str, str]]

    def run(self, llm: ChatOpenAI, code: str) -> str:
        output = ""
        for tup in self.template:
            if len(tup) == 1:  # Top level header
                output += f"{tup[0]}\n"
            else:  # 2nd level, prompt pair
                section_title, section_prompt = tup
                human_prompt = f"{section_prompt}\n\nCode:\n\n{code}"
                content = llm.generate_response(self.system_prompt, human_prompt)
                output += f"{section_title}\n{content}\n"

        return output


def file_long_from_code(
    llm: ChatOpenAI, file_name: str, codebase_name: str, path: str | Path, code: str
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH / "prompt_templates/files/long_from_code.txt"
    )
    human_prompt = f"`{file_name}` in codebase `{codebase_name}` with path `{str(path)}`:\n\n{code}"
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
    logging.info(f"Incorporating `{node.root_rel_path}`")

    if len(source_code.strip()) == 0:
        description = "Empty file (no analyzable contents)."
        success = False
        results = _return_with_simple_message(
            message=description,
        )
        return success, results
    chunks = chunk_str(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, str_in=source_code
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
        # TODO: Decide how/when/if to fold use of the code map for longer files like this.
        logging.info(f"Processing {len(chunks)} chunks for `{node.root_rel_path}`")
        print(f"Processing {len(chunks)} chunks for `{node.root_rel_path}` ...")
        # if use_async:
        #     with FastShutdownThreadPoolExecutor(max_workers=max_workers) as executor:
        #         futures = {
        #             executor.submit(
        #                 file_chunk_description,
        #                 llm,
        #                 node.name,
        #                 codebase_name,
        #                 node.root_rel_path,
        #                 c,
        #             ): idx
        #             for idx, c in enumerate(chunks)
        #         }
        #         # Make sure the original chunk order is preserved.
        #         results = [
        #             (futures[future], future.result())
        #             for future in concurrent.futures.as_completed(futures.keys())
        #         ]
        #         chunk_detailed_descriptions = [
        #             r for (_idx, r) in sorted(results, key=lambda tup: tup[0])
        #         ]
        #         # Compression steps, if needed.
        #         aggregated_descriptions = ""
        #         for idx, c in enumerate(chunk_detailed_descriptions, start=1):
        #             aggregated_descriptions += f"File chunk {idx} description for file `{node.name}`:\n\n{c}\n\n"
        #         compression_idx = 0
        #         while len(aggregated_descriptions) >= chunk_size:
        #             chunks = chunk_str(
        #                 chunk_size=chunk_size,
        #                 chunk_overlap=chunk_overlap,
        #                 str_in=aggregated_descriptions,
        #             )
        #             logging.info(
        #                 f"Compressing {len(chunks)} chunk descriptions for `{node.name}`"
        #             )
        #             print(
        #                 f"Compressing {len(chunks)} chunk descriptions for `{node.name}`"
        #             )
        #             futures = {
        #                 executor.submit(
        #                     file_compress_chunks,
        #                     llm,
        #                     node.name,
        #                     c,
        #                 ): idx
        #                 for idx, c in enumerate(chunks)
        #             }
        #             # Make sure the original chunk order is preserved.
        #             results = [
        #                 (futures[future], future.result())
        #                 for future in concurrent.futures.as_completed(futures.keys())
        #             ]
        #             chunk_detailed_descriptions = [
        #                 r for (_idx, r) in sorted(results, key=lambda tup: tup[0])
        #             ]
        #             aggregated_descriptions = ""
        #             for idx, c in enumerate(chunk_detailed_descriptions, start=1):
        #                 aggregated_descriptions += f"File chunk {idx} description for file `{node.name}`:\n\n{c}"
        #             compression_idx += 1
        #             if compression_idx >= compression_loop_max_itr:
        #                 if raise_hard_errors:
        #                     raise ValueError(
        #                         f"Compression loop max iteration ({compression_loop_max_itr}) reached for file `{node.name}`"
        #                     )
        #                 else:
        #                     logging.warning(
        #                         f"Compression loop max iteration ({compression_loop_max_itr}) reached for file `{node.name}`"
        #                     )
        #                     print(
        #                         f"WARNING: Compression loop max iteration ({compression_loop_max_itr}) reached for file `{node.name}`"
        #                     )
        #                     description = "File too large to process."
        #                     success = False
        #                     results = _return_with_simple_message(
        #                         message=description,
        #                         file_node=node,
        #                         file_content=file_content,
        #                         to_disk_dir=to_disk_dir,
        #                     )
        #                     return (success, results)
        # else:
        chunk_detailed_descriptions = []
        num_chunks = len(chunks)
        for idx, c in enumerate(chunks):
            try:
                chunk_detailed_descriptions.append(
                    file_chunk_description(
                        llm=llm,
                        file_name=node.root_rel_path.name,
                        codebase_name=codebase_name,
                        path=node.root_rel_path,
                        code_chunk=c,
                    )
                )
                logging.info(
                    f"Source code chunk {idx + 1}/{num_chunks} processed for file `{node.root_rel_path}`"
                )
                print(
                    f"Source code chunk {idx + 1}/{num_chunks} processed for file `{node.root_rel_path}`"
                )
            except openai.BadRequestError:
                description = "Could not process file"
                success = False
                results = _return_with_simple_message(
                    message=description,
                )
                return success, results

        # Compression steps, if needed.
        aggregated_descriptions = ""
        for idx, c in enumerate(chunk_detailed_descriptions, start=1):
            aggregated_descriptions += f"File chunk {idx} description for file `{node.root_rel_path}`:\n\n{c}\n\n"
        compression_idx = 0
        while len(aggregated_descriptions) >= chunk_size:
            chunks = chunk_str(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                str_in=aggregated_descriptions,
            )
            num_chunks = len(chunks)
            logging.info(
                f"Compressing {len(chunks)} chunk descriptions for file `{node.root_rel_path}`"
            )
            print(
                f"Compressing {len(chunks)} chunk descriptions for file `{node.root_rel_path}`"
            )
            chunk_detailed_descriptions = []
            for idx, c in enumerate(chunks):
                chunk_detailed_descriptions.append(
                    file_compress_chunks(
                        llm=llm, file_name=node.root_rel_path.name, description_chunk=c
                    )
                )
                logging.info(
                    f"Compression chunk {idx + 1}/{num_chunks} for compression iteration {compression_idx + 1} processed for file `{node.root_rel_path}`"
                )
                print(
                    f"Compression chunk {idx + 1}/{num_chunks} for compression iteration {compression_idx + 1} processed for file `{node.root_rel_path}`"
                )
            aggregated_descriptions = ""
            for idx, c in enumerate(chunk_detailed_descriptions, start=1):
                aggregated_descriptions += f"File chunk {idx} description for file `{node.root_rel_path.name}`:\n\n{c}"
            compression_idx += 1
            if compression_idx >= compression_loop_max_itr:
                if raise_hard_errors:
                    raise ValueError(
                        f"Compression loop max iteration ({compression_loop_max_itr}) reached for file `{node.root_rel_path}`"
                    )
                else:
                    logging.warning(
                        f"Compression loop max iteration ({compression_loop_max_itr}) reached for file `{node.root_rel_path}`"
                    )
                    print(
                        f"WARNING: Compression loop max iteration ({compression_loop_max_itr}) reached for file `{node.root_rel_path}`"
                    )
                    description = "File too large to process."
                    success = False
                    results = _return_with_simple_message(
                        message=description,
                    )
                    return (success, results)

        # Now ready to generate final documentation content.
        file_description_long = file_long_from_chunk_descriptions(
            llm=llm,
            chunks=chunk_detailed_descriptions,
            file_name=node.root_rel_path.name,
            codebase_name=codebase_name,
        )
        file_description_single_sentence = file_single_sentence_from_chunk_descriptions(
            llm=llm,
            chunks=chunk_detailed_descriptions,
            file_name=node.root_rel_path.name,
            codebase_name=codebase_name,
        )
        file_description_single_paragraph = (
            file_single_paragraph_from_chunk_descriptions(
                llm=llm,
                chunks=chunk_detailed_descriptions,
                file_name=node.root_rel_path.name,
                codebase_name=codebase_name,
            )
        )
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
            long_template = Template(
                system_prompt=SIMPLE_START_SYSTEM_PROMPT, template=SIMPLE_START_TEMPLATE
            )
            file_description_long = long_template.run(llm=llm, code=source_code)
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
        except openai.BadRequestError:
            # TODO: this is a hack. Should rethink the tokenizing
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
