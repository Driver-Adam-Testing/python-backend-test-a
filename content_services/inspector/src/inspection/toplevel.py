import concurrent.futures
from pathlib import Path
from typing import Any

from tqdm import tqdm
from utils.dag import LiteNode, NodeKind
from utils.io import (
    get_prompt_template,
)
from utils.llm import chunk_str
from utils.models import ChatOpenAI
from utils.prompts import (
    GENERAL_STE_STYLE_INSTRUCTION,
    NO_RESTATEMENT_STYLE_INSTRUCTION,
    TERSE_TWITTER_SINGLE_SENTENCE_STYLE_INSTRUCTION,
    Prompt,
    RawPromptComponent,
)
from utils.threadpool import FastShutdownThreadPoolExecutor

PARENT_PATH = Path(__file__).parent


def toplevel_chunk_description(
    llm: ChatOpenAI,
    codebase_name: str,
    description_chunk: str,
) -> str:
    system_prompt = (
        Prompt.empty()
        .append(
            RawPromptComponent.from_raw_str(
                get_prompt_template(
                    PARENT_PATH / "prompt_templates/toplevel/chunk_description.txt"
                )
            ).resolve()
        )
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str(sep="\n\n")
    )
    user_prompt = f"Chunk of content descriptions for codebase `{codebase_name}`:\n\n{description_chunk}"
    return llm.generate_response(system_prompt, user_prompt)


def toplevel_compress_chunks(
    llm: ChatOpenAI,
    codebase_name: str,
    description_chunk: str,
) -> str:
    system_prompt = (
        Prompt.empty()
        .append(
            RawPromptComponent.from_raw_str(
                get_prompt_template(
                    PARENT_PATH / "prompt_templates/toplevel/compress_chunks.txt"
                )
            ).resolve()
        )
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str(sep="\n\n")
    )
    user_prompt = f"Chunk of module subset descriptions for codebase `{codebase_name}`:\n\n{description_chunk}"
    return llm.generate_response(system_prompt, user_prompt)


def toplevel_long_from_chunk_descriptions(
    llm: ChatOpenAI,
    codebase_name: str,
    data: str,
) -> str:
    system_prompt = (
        Prompt.empty()
        .append(
            RawPromptComponent.from_raw_str(
                get_prompt_template(
                    PARENT_PATH
                    / "prompt_templates/toplevel/long_from_chunk_descriptions.txt"
                )
            ).resolve()
        )
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str(sep="\n\n")
    )
    user_prompt = (
        f"Chunk of module subset descriptions for codebase {codebase_name}:\n\n{data}"
    )
    return llm.generate_response(system_prompt, user_prompt)


def toplevel_terse_sentence_from_chunk_descriptions(
    llm: ChatOpenAI,
    data: str,
    codebase_name: str,
) -> str:
    system_prompt = (
        Prompt.empty()
        .append(
            RawPromptComponent.from_raw_str(
                get_prompt_template(
                    PARENT_PATH
                    / "prompt_templates/toplevel/terse_sentence_from_chunk_descriptions.txt"
                )
            ).resolve()
        )
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str(sep="\n\n")
    )
    user_prompt = (
        Prompt.empty()
        .append(
            RawPromptComponent.from_raw_str(
                f"Chunk of module subset descriptions for codebase {codebase_name}\n\n{data}"
            ).resolve()
        )
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION)
        .append(TERSE_TWITTER_SINGLE_SENTENCE_STYLE_INSTRUCTION)
        .into_str("\n\n")
    )
    return llm.generate_response(system_prompt, user_prompt)


def toplevel_single_sentence_from_chunk_descriptions(
    llm: ChatOpenAI,
    data: str,
    codebase_name: str,
) -> str:
    system_prompt = (
        Prompt.empty()
        .append(
            RawPromptComponent.from_raw_str(
                get_prompt_template(
                    PARENT_PATH
                    / "prompt_templates/toplevel/single_sentence_from_chunk_descriptions.txt"
                )
            ).resolve()
        )
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str(sep="\n\n")
    )
    user_prompt = (
        Prompt.empty()
        .append(
            RawPromptComponent.from_raw_str(
                f"Chunk of module subset descriptions for codebase {codebase_name}\n\n{data}"
            ).resolve()
        )
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION)
        .into_str(sep="\n\n")
    )
    return llm.generate_response(system_prompt, user_prompt)


def toplevel_single_paragraph_from_chunk_descriptions(
    llm: ChatOpenAI,
    data: str,
    codebase_name: str,
) -> str:
    system_prompt = (
        Prompt.empty()
        .append(
            RawPromptComponent.from_raw_str(
                get_prompt_template(
                    PARENT_PATH
                    / "prompt_templates/toplevel/single_paragraph_from_chunk_descriptions.txt"
                )
            ).resolve()
        )
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str(sep="\n\n")
    )
    user_prompt = (
        Prompt.empty()
        .append(
            RawPromptComponent.from_raw_str(
                f"Chunk of module subset descriptions for codebase {codebase_name}\n\n{data}"
            ).resolve()
        )
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION)
        .into_str(sep="\n\n")
    )
    return llm.generate_response(system_prompt, user_prompt)


def toplevel_long_from_long_descriptions(
    llm: ChatOpenAI,
    codebase_name: str,
    data: str,
) -> str:
    system_prompt = (
        Prompt.empty()
        .append(
            RawPromptComponent.from_raw_str(
                get_prompt_template(
                    PARENT_PATH
                    / "prompt_templates/toplevel/long_from_long_descriptions.txt"
                )
            ).resolve()
        )
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str(sep="\n\n")
    )
    user_prompt = f"Codebase name: {codebase_name}\n\n{data}"
    return llm.generate_response(system_prompt, user_prompt)


def toplevel_terse_sentence_from_long_descriptions(
    llm: ChatOpenAI, codebase_name: str, data: str
) -> str:
    system_prompt = (
        Prompt.empty()
        .append(
            RawPromptComponent.from_raw_str(
                get_prompt_template(
                    PARENT_PATH
                    / "prompt_templates/toplevel/terse_sentence_from_long_descriptions.txt"
                )
            ).resolve()
        )
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str(sep="\n\n")
    )
    user_prompt = (
        Prompt.empty()
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION)
        .append(TERSE_TWITTER_SINGLE_SENTENCE_STYLE_INSTRUCTION)
        .append(
            RawPromptComponent.from_raw_str(f"Codebase name: {codebase_name}\n\n{data}")
        )
        .into_str(sep="\n\n")
    )
    return llm.generate_response(system_prompt, user_prompt)


def toplevel_single_sentence_from_long_descriptions(
    llm: ChatOpenAI, codebase_name: str, data: str
) -> str:
    system_prompt = (
        Prompt.empty()
        .append(
            RawPromptComponent.from_raw_str(
                get_prompt_template(
                    PARENT_PATH
                    / "prompt_templates/toplevel/single_sentence_from_long_descriptions.txt"
                )
            ).resolve()
        )
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str(sep="\n\n")
    )
    user_prompt = (
        Prompt.empty()
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION)
        .append(
            RawPromptComponent.from_raw_str(
                f"Codebase name: {codebase_name}\n\n{data}"
            ).resolve()
        )
        .into_str(sep="\n\n")
    )
    return llm.generate_response(system_prompt, user_prompt)


def toplevel_single_paragraph_from_long_descriptions(
    llm: ChatOpenAI, codebase_name: str, data: str
) -> str:
    system_prompt = (
        Prompt.empty()
        .append(
            RawPromptComponent.from_raw_str(
                get_prompt_template(
                    PARENT_PATH
                    / "prompt_templates/toplevel/single_paragraph_from_long_descriptions.txt"
                )
            ).resolve()
        )
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str(sep="\n\n")
    )
    user_prompt = (
        Prompt.empty()
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION)
        .append(
            RawPromptComponent.from_raw_str(
                f"Codebase name: {codebase_name}\n\n{data}"
            ).resolve()
        )
        .into_str(sep="\n\n")
    )
    return llm.generate_response(system_prompt, user_prompt)


def comprehend_codebase_top_down(
    llm: ChatOpenAI,
    docs: dict[LiteNode, dict[str, Any]],
    codebase_name: str,
    chunk_size: int,
    chunk_overlap: int,
    max_workers: int,
    include_exploratory_generation: bool,
    compression_loop_max_itr: int,
) -> dict[str, Any]:
    print(f"Aggregating and incorporating module info for codebase `{codebase_name}`")
    codebase_content = ""
    for node in docs:
        if node.kind == NodeKind.FILE:
            codebase_content += (
                f"File `{node.root_rel_path.name}` at `{node.root_rel_path}` "
                f"description:\n\n{docs[node]['short']['single_paragraph']}\n\n"
            )
        elif node.kind == NodeKind.SUB_FOLDER or node.kind == NodeKind.ROOT_FOLDER:
            codebase_content += (
                f"Folder `{node.root_rel_path.name}` at `{node.root_rel_path}` "
                f"description:\n\n{docs[node]['short']['single_paragraph']}\n\n"
            )
        else:
            raise Exception("Unreachable")

    chunks = chunk_str(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, str_in=codebase_content
    )
    print(f"Number of top-level chunks: {len(chunks)}")
    print(f"Number of initial chunks for top-level content: {len(chunks)}")
    print(f"Processing {len(chunks)} initial chunks for top-level content")
    if len(chunks) > 1:
        with FastShutdownThreadPoolExecutor(max_workers=max_workers) as executor:
            num_chunks = len(chunks)
            futures = {
                executor.submit(toplevel_chunk_description, llm, codebase_name, c): idx
                for idx, c in enumerate(chunks)
            }
            # Make sure the original chunk order is preserved.
            results = []
            with tqdm(total=num_chunks, desc="Top-level", colour="green") as pbar:
                for idx, future in enumerate(
                    concurrent.futures.as_completed(futures.keys())
                ):
                    res = future.result()
                    if res is not None:
                        print(
                            f"Processed {idx}/{num_chunks - 1} initial top-level chunks"
                        )
                        results.append((futures[future], res))
                    pbar.update(1)
            chunk_detailed_descriptions = [
                r for (_idx, r) in sorted(results, key=lambda tup: tup[0])
            ]

        compression_idx = 0
        aggregated_descriptions = ""
        for idx, c in enumerate(chunk_detailed_descriptions, start=1):
            aggregated_descriptions += f"Content subset {idx} description for codebase {codebase_name}:\n\n{c}\n\n"
        while (
            len(aggregated_descriptions) >= chunk_size
            and compression_idx < compression_loop_max_itr
        ):
            print(f"\n\nAggregated description length: {len(aggregated_descriptions)}")
            print(
                f"\n\nAggregated description length in compression iteration {compression_idx}: {len(aggregated_descriptions)}"
            )
            chunks = chunk_str(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                str_in=aggregated_descriptions,
            )
            with FastShutdownThreadPoolExecutor(max_workers=max_workers) as executor:
                num_chunks = len(chunks)
                futures = {
                    executor.submit(
                        toplevel_compress_chunks, llm, codebase_name, c
                    ): idx
                    for idx, c in enumerate(chunks)
                }
                # Make sure the original chunk order is preserved.
                results = []
                with tqdm(total=len(chunks), colour="green") as pbar:
                    for idx, future in enumerate(
                        concurrent.futures.as_completed(futures.keys())
                    ):
                        res = future.result()
                        if res is not None:
                            print(
                                f"Processed {idx}/{num_chunks - 1} chunks for top-level content in compression iteration {compression_idx}"
                            )
                            results.append((futures[future], res))
                        pbar.update(1)
                chunk_detailed_descriptions = [
                    r for (_idx, r) in sorted(results, key=lambda tup: tup[0])
                ]
            aggregated_descriptions = ""
            for idx, c in enumerate(chunk_detailed_descriptions, start=1):
                aggregated_descriptions += f"Content subset {idx} description for codebase {codebase_name}:\n\n{c}\n\n"
            compression_idx += 1

        print(f"`chunk_detailed_descriptions`: {chunk_detailed_descriptions}")
        aggregation_state = "chunks"
        data = aggregated_descriptions
        _ir = [aggregation_state, data]
    else:
        aggregation_state = "no_chunks"
        data = codebase_content
        _ir = [aggregation_state, data]

    print("Generating final top-level content ...")
    with FastShutdownThreadPoolExecutor(max_workers=max_workers) as executor:
        if aggregation_state == "chunks":
            long_future = executor.submit(
                toplevel_long_from_chunk_descriptions,
                llm,
                codebase_name,
                data,
            )
            terse_sentence_future = executor.submit(
                toplevel_terse_sentence_from_chunk_descriptions,
                llm,
                data,
                codebase_name,
            )
            single_sentence_future = executor.submit(
                toplevel_single_sentence_from_chunk_descriptions,
                llm,
                data,
                codebase_name,
            )
            single_paragraph_future = executor.submit(
                toplevel_single_paragraph_from_chunk_descriptions,
                llm,
                data,
                codebase_name,
            )
        else:
            long_future = executor.submit(
                toplevel_long_from_long_descriptions,
                llm,
                codebase_name,
                data,
            )
            terse_sentence_future = executor.submit(
                toplevel_terse_sentence_from_long_descriptions,
                llm,
                codebase_name,
                data,
            )
            single_sentence_future = executor.submit(
                toplevel_single_sentence_from_long_descriptions,
                llm,
                codebase_name,
                data,
            )
            single_paragraph_future = executor.submit(
                toplevel_single_paragraph_from_long_descriptions,
                llm,
                codebase_name,
                data,
            )

        long = long_future.result()
        terse_sentence = terse_sentence_future.result()
        single_sentence = single_sentence_future.result()
        single_paragraph = single_paragraph_future.result()

    terse_sentence = terse_sentence.replace("\x00", "")
    single_sentence = single_sentence.replace("\x00", "")
    single_paragraph = single_paragraph.replace("\x00", "")
    long = long.replace("\x00", "")

    short_descriptions = {
        "terse_sentence": terse_sentence,
        "single_sentence": single_sentence,
        "single_paragraph": single_paragraph,
    }
    print(f"Codebase short description:\n{short_descriptions['single_paragraph']}")

    return {
        "aggregated_description": data,
        "short": short_descriptions,
        "long": long,
    }
