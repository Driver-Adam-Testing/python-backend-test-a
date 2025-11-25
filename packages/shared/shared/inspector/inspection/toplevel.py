import asyncio
import concurrent.futures
from pathlib import Path
from typing import Any

from database.models_enums import ContentKind
from shared.agent.chat_openai import ChatOpenAI
from shared.agent.chat_openai_async import ChatOpenAI as AsyncChatOpenAI
from shared.inspector.utils.dag import LiteNode, NodeKind
from shared.inspector.utils.io import (
    get_prompt_template,
)
from shared.inspector.utils.llm import chunk_str
from shared.inspector.utils.tags.codebase_wide import (
    CodebaseAudienceScores,
    CodebaseDomainScores,
    CodebaseKindScores,
)
from shared.inspector.utils.tags.entry_point import EntryPoints
from shared.inspector.utils.threadpool import FastShutdownThreadPoolExecutor
from shared.prompts.structured_prompting import (
    DESCRIBE_WITH_CATEGORY_AND_ACTION_VERB,
    GENERAL_STE_STYLE_INSTRUCTION,
    NO_MARKDOWN_ONLY_RAW_TEXT_FORMATTING,
    TERSE_TWITTER_SINGLE_SENTENCE_STYLE_INSTRUCTION,
    Component,
    Prompt,
)
from tqdm import tqdm

PARENT_PATH = Path(__file__).parent


def toplevel_chunk_description(
    llm: ChatOpenAI,
    codebase_name: str,
    description_chunk: str,
) -> str:
    system_prompt = (
        Prompt.empty()
        .append(
            Component(
                string=get_prompt_template(
                    PARENT_PATH / "prompt_templates/toplevel/chunk_description.txt"
                )
            )
        )
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str()
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
            Component(
                string=get_prompt_template(
                    PARENT_PATH / "prompt_templates/toplevel/compress_chunks.txt"
                )
            )
        )
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str()
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
            Component(
                string=get_prompt_template(
                    PARENT_PATH
                    / "prompt_templates/toplevel/long_from_chunk_descriptions.txt"
                )
            )
        )
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str()
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
            Component(
                string=get_prompt_template(
                    PARENT_PATH
                    / "prompt_templates/toplevel/terse_sentence_from_chunk_descriptions.txt"
                )
            )
        )
        .append(NO_MARKDOWN_ONLY_RAW_TEXT_FORMATTING)
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str()
    )
    user_prompt = (
        Prompt.empty()
        .append(DESCRIBE_WITH_CATEGORY_AND_ACTION_VERB)
        .append(TERSE_TWITTER_SINGLE_SENTENCE_STYLE_INSTRUCTION)
        .append(
            Component(
                string=f"Chunk of module subset descriptions for codebase {codebase_name}\n\n{data}"
            )
        )
        .into_str()
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
            Component(
                string=get_prompt_template(
                    PARENT_PATH
                    / "prompt_templates/toplevel/single_sentence_from_chunk_descriptions.txt"
                )
            )
        )
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str()
    )
    user_prompt = (
        Prompt.empty()
        .append(
            Component(
                string=f"Chunk of module subset descriptions for codebase {codebase_name}\n\n{data}"
            )
        )
        .append(DESCRIBE_WITH_CATEGORY_AND_ACTION_VERB)
        .into_str()
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
            Component(
                string=get_prompt_template(
                    PARENT_PATH
                    / "prompt_templates/toplevel/single_paragraph_from_chunk_descriptions.txt"
                )
            )
        )
        .append(NO_MARKDOWN_ONLY_RAW_TEXT_FORMATTING)
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str()
    )
    user_prompt = (
        Prompt.empty()
        .append(DESCRIBE_WITH_CATEGORY_AND_ACTION_VERB)
        .append(
            Component(
                string=f"Chunk of module subset descriptions for codebase {codebase_name}\n\n{data}"
            )
        )
        .into_str()
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
            Component(
                string=get_prompt_template(
                    PARENT_PATH
                    / "prompt_templates/toplevel/long_from_long_descriptions.txt"
                )
            )
        )
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str()
    )
    user_prompt = f"Codebase name: {codebase_name}\n\n{data}"
    return llm.generate_response(system_prompt, user_prompt)


def toplevel_terse_sentence_from_long_descriptions(
    llm: ChatOpenAI, codebase_name: str, data: str
) -> str:
    system_prompt = (
        Prompt.empty()
        .append(
            Component(
                string=get_prompt_template(
                    PARENT_PATH
                    / "prompt_templates/toplevel/terse_sentence_from_long_descriptions.txt"
                )
            )
        )
        .append(NO_MARKDOWN_ONLY_RAW_TEXT_FORMATTING)
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str()
    )
    user_prompt = (
        Prompt.empty()
        .append(DESCRIBE_WITH_CATEGORY_AND_ACTION_VERB)
        .append(TERSE_TWITTER_SINGLE_SENTENCE_STYLE_INSTRUCTION)
        .append(Component(string=f"Codebase name: {codebase_name}\n\n{data}"))
        .into_str()
    )
    return llm.generate_response(system_prompt, user_prompt)


def toplevel_single_sentence_from_long_descriptions(
    llm: ChatOpenAI, codebase_name: str, data: str
) -> str:
    system_prompt = (
        Prompt.empty()
        .append(
            Component(
                string=get_prompt_template(
                    PARENT_PATH
                    / "prompt_templates/toplevel/single_sentence_from_long_descriptions.txt"
                )
            )
        )
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str()
    )
    user_prompt = (
        Prompt.empty()
        .append(DESCRIBE_WITH_CATEGORY_AND_ACTION_VERB)
        .append(Component(string=f"Codebase name: {codebase_name}\n\n{data}"))
        .into_str()
    )
    return llm.generate_response(system_prompt, user_prompt)


def toplevel_single_paragraph_from_long_descriptions(
    llm: ChatOpenAI, codebase_name: str, data: str
) -> str:
    system_prompt = (
        Prompt.empty()
        .append(
            Component(
                string=get_prompt_template(
                    PARENT_PATH
                    / "prompt_templates/toplevel/single_paragraph_from_long_descriptions.txt"
                )
            )
        )
        .append(NO_MARKDOWN_ONLY_RAW_TEXT_FORMATTING)
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str()
    )
    user_prompt = (
        Prompt.empty()
        .append(DESCRIBE_WITH_CATEGORY_AND_ACTION_VERB)
        .append(Component(string=f"Codebase name: {codebase_name}\n\n{data}"))
        .into_str()
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


def tag_codebase(
    llm: ChatOpenAI,
    docs: dict[LiteNode, dict[str, Any]],
    content_kinds: set[ContentKind],
) -> dict[ContentKind, list[dict]]:
    results = {}
    if ContentKind.CODEBASE_KINDS in content_kinds:
        results[ContentKind.CODEBASE_KINDS] = [
            dict(CodebaseKindScores.from_llm(llm=llm, docs=docs).sorted_list)
        ]
        print(f"Codebase kind scores:\n\n{results[ContentKind.CODEBASE_KINDS]}")
    if ContentKind.CODEBASE_DOMAINS in content_kinds:
        results[ContentKind.CODEBASE_DOMAINS] = [
            dict(CodebaseDomainScores.from_llm(llm=llm, docs=docs).sorted_list)
        ]
        print(f"Codebase domain scores:\n\n{results[ContentKind.CODEBASE_DOMAINS]}")
    if ContentKind.CODEBASE_AUDIENCES in content_kinds:
        results[ContentKind.CODEBASE_AUDIENCES] = [
            dict(CodebaseAudienceScores.from_llm(llm=llm, docs=docs).sorted_list)
        ]
        print(f"Codebase audience scores:\n\n{results[ContentKind.CODEBASE_AUDIENCES]}")
    if ContentKind.CODEBASE_ENTRY_POINTS in content_kinds:
        entry_points = asyncio.run(
            EntryPoints.from_llm(
                llm=AsyncChatOpenAI(
                    model="gpt-4o-2024-08-06", temperature=0, request_timeout=500
                ),
                docs=docs,
                n=3,
            )
        )
        results[ContentKind.CODEBASE_ENTRY_POINTS] = [
            e.model_dump() for e in entry_points.entry_points
        ]
        print(f"Codebase entry points:\n\n{results[ContentKind.CODEBASE_ENTRY_POINTS]}")

    return results
