import concurrent.futures
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any

from utils.dag import LiteNode, NodeKind
from utils.io import get_prompt_template
from utils.llm import chunk_str, num_tokens_from_messages_open_ai
from utils.models import ChatOpenAI
from utils.threadpool import FastShutdownThreadPoolExecutor

PARENT_PATH = Path(__file__).parent
MAX_TOKENS_FOR_PRIORITY_ORDERING = 10_000


@dataclass(frozen=True)
class ContentDocs:
    docs: dict[str, Any]


class AggregationState(Enum):
    CHILD_LIST = auto()
    SINGLE_CHUNK = auto()
    MANY_CHUNKS = auto()


def folder_item_priority_ordering(
    llm: ChatOpenAI,
    raw_list_str: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH / "prompt_templates/folders/item_priority_ordering.txt"
    )
    human_prompt = raw_list_str
    return llm.generate_response(system_prompt, human_prompt)


def folder_chunk_description(
    llm: ChatOpenAI,
    folder_name: str,
    codebase_name: str,
    description_chunk: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH / "prompt_templates/folders/chunk_description.txt"
    )
    human_prompt = (
        f"Chunk of child descriptions for folder `{folder_name}` in codebase `{codebase_name}`:"
        f"\n\n{description_chunk}"
    )
    return llm.generate_response(system_prompt, human_prompt)


def folder_compress_chunks(
    llm: ChatOpenAI,
    folder_name: str,
    codebase_name: str,
    description_chunk: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH / "prompt_templates/folders/compress_chunks.txt"
    )
    human_prompt = (
        f"Chunk of child subset descriptions for folder `{folder_name}` in codebase `{codebase_name}`:"
        f"\n\n{description_chunk}"
    )
    return llm.generate_response(system_prompt, human_prompt)


def folder_single_sentence_from_child_list(
    llm: ChatOpenAI,
    folder_name: str,
    codebase_name: str,
    data: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH / "prompt_templates/folders/single_sentence_from_child_list.txt"
    )
    human_prompt = ""
    human_prompt += f"Folder `{folder_name}` in codebase `{codebase_name}` child content:\n\n{data}\n\n"
    return llm.generate_response(system_prompt, human_prompt)


def folder_single_paragraph_from_child_list(
    llm: ChatOpenAI,
    folder_name: str,
    codebase_name: str,
    data: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH / "prompt_templates/folders/single_paragraph_from_child_list.txt"
    )
    human_prompt = ""
    human_prompt += f"Folder `{folder_name}` in codebase `{codebase_name}` child content:\n\n{data}\n\n"
    return llm.generate_response(system_prompt, human_prompt)


def folder_long_from_chunk_descriptions(
    llm: ChatOpenAI,
    folder_name: str,
    codebase_name: str,
    data: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH / "prompt_templates/folders/long_from_chunk_descriptions.txt"
    )
    human_prompt = data
    return llm.generate_response(system_prompt, human_prompt)


def folder_single_sentence_from_chunk_descriptions(
    llm: ChatOpenAI,
    folder_name: str,
    codebase_name: str,
    data: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/folders/single_sentence_from_chunk_descriptions.txt"
    )
    human_prompt = data
    return llm.generate_response(system_prompt, human_prompt)


def folder_single_paragraph_from_chunk_descriptions(
    llm: ChatOpenAI,
    folder_name: str,
    codebase_name: str,
    data: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/folders/single_paragraph_from_chunk_descriptions.txt"
    )
    human_prompt = data
    return llm.generate_response(system_prompt, human_prompt)


def folder_long_from_long_descriptions(
    llm: ChatOpenAI,
    folder_name: str,
    codebase_name: str,
    data: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH / "prompt_templates/folders/long_from_long_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += (
        f"Folder `{folder_name}` in codebase `{codebase_name}` content:\n\n{data}\n\n"
    )
    return llm.generate_response(system_prompt, human_prompt)


def folder_single_sentence_from_long_descriptions(
    llm: ChatOpenAI,
    folder_name: str,
    codebase_name: str,
    data: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/folders/single_sentence_from_long_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += (
        f"Folder `{folder_name}` in codebase `{codebase_name}` content:\n\n{data}\n\n"
    )
    return llm.generate_response(system_prompt, human_prompt)


def folder_single_paragraph_from_long_descriptions(
    llm: ChatOpenAI,
    folder_name: str,
    codebase_name: str,
    data: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/folders/single_paragraph_from_long_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += (
        f"Folder `{folder_name}` in codebase `{codebase_name}` content:\n\n{data}\n\n"
    )
    return llm.generate_response(system_prompt, human_prompt)


def _return_with_simple_message(message: str, folder_node: LiteNode) -> dict[str, any]:
    long_description = message
    short_descriptions = {
        "single_sentence": message,
        "single_paragraph": message,
    }
    return {
        "short": short_descriptions,
        "long": long_description,
    }


def comprehend_folder_top_down(
    llm: ChatOpenAI,
    codebase_name: str,
    node: LiteNode,
    chunk_size: int,
    chunk_overlap: int,
    max_workers: int,
    child_nodes_to_docs: dict[LiteNode, ContentDocs],
    compression_loop_max_itr: int,
    raise_hard_errors: bool = True,
    redundant_folder_flag: bool = False,
    use_async: bool = False,
) -> dict[str, any]:
    folder_name = node.root_rel_path.name
    print(
        f"Incorporating `{node.root_rel_path}` for repo `{codebase_name}` ({len(child_nodes_to_docs)} child nodes)"
    )
    # Handle empty directories.
    if len(child_nodes_to_docs) == 0:
        description = "No analyzable contents."
        return _return_with_simple_message(message=description, folder_node=node)

    # Handle redundant folders.
    if redundant_folder_flag:
        description = "No unique content; see single subfolder."
        return _return_with_simple_message(message=description, folder_node=node)

    # Base all content generation on a list of all child single sentence descriptions.
    print(f"Aggregating child info for folder `{folder_name}`")
    child_single_sentence_descriptions = {
        k: v["short"]["single_sentence"] for k, v in child_nodes_to_docs.items()
    }
    child_folder_list = ""
    child_file_list = ""
    for k, v in child_single_sentence_descriptions.items():
        if k.kind == NodeKind.FILE:
            child_file_list += f"- **{k.root_rel_path.name}**: {v}\n"
        else:  # subfolder or root folder
            child_folder_list += f"- **{k.root_rel_path.name}**: {v}\n"
    if child_folder_list:
        folder_prefix = "## Folders\n"
        folder_list_tokens = num_tokens_from_messages_open_ai(
            [child_folder_list], llm.model
        )
        if folder_list_tokens < MAX_TOKENS_FOR_PRIORITY_ORDERING:
            child_folder_list_ordered = folder_item_priority_ordering(
                llm=llm, raw_list_str=f"{folder_prefix}{child_folder_list}"
            )
        else:
            child_folder_list_ordered = f"{folder_prefix}{child_folder_list}"
    else:
        child_folder_list_ordered = ""
    if child_file_list:
        file_prefix = "## Files\n"
        file_list_tokens = num_tokens_from_messages_open_ai(
            [child_file_list], llm.model
        )
        if file_list_tokens < MAX_TOKENS_FOR_PRIORITY_ORDERING:
            child_file_list_ordered = folder_item_priority_ordering(
                llm=llm, raw_list_str=f"{file_prefix}{child_file_list}"
            )
        else:
            child_file_list_ordered = f"{file_prefix}{child_file_list}"
    else:
        child_file_list_ordered = ""
    completed_child_lists = f"{child_folder_list_ordered}\n{child_file_list_ordered}"

    # Proceed according to child list content length relative to chunk size.
    print(f"Checking if compression is required for folder `{folder_name}` content...")
    list_chunks: list[str] = chunk_str(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, str_in=completed_child_lists
    )
    if len(list_chunks) > 1:
        # For 128k+ token context window models, egregiously large number of children.
        # Fall back to original compression loop approach in this case.
        print(f"Aggregating and incorporating child info for folder `{folder_name}`")
        child_content = ""
        for k, v in child_nodes_to_docs.items():
            entity = "File" if k.kind == NodeKind.FILE else "Folder"
            long = v["long"]
            child_content += (
                f"{entity} `{k.root_rel_path.name}` description:\n\n{long}\n\n"
            )
        chunks: list[str] = chunk_str(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap, str_in=child_content
        )
        num_chunks = len(chunks)
        # TODO: Consider parity with file content generation where there is a
        # TODO: check against a max number of chunks.
        if num_chunks > 1:
            aggregation_state = AggregationState.MANY_CHUNKS
            print(f"Number of initial chunks for folder `{folder_name}`: {num_chunks}")
            print(f"Processing {len(chunks)} chunks for folder `{folder_name}` ...")
            if use_async:
                with FastShutdownThreadPoolExecutor(
                    max_workers=max_workers
                ) as executor:
                    futures = {
                        executor.submit(
                            folder_chunk_description,
                            llm,
                            folder_name,
                            codebase_name,
                            c_str,
                        ): idx
                        for idx, c_str in enumerate(chunks)
                    }
                    # Make sure the original chunk order is preserved.
                    results = []
                    for idx, future in enumerate(
                        concurrent.futures.as_completed(futures.keys())
                    ):
                        res = future.result()
                        if res is not None:
                            print(
                                f"Processed {idx}/{num_chunks-1} initial chunks for folder `{folder_name}`"
                            )
                            results.append((futures[future], res))
                    chunk_detailed_descriptions: list[str] = [
                        r for (_idx, r) in sorted(results, key=lambda tup: tup[0])
                    ]

                aggregated_descriptions = ""
                for idx, c_str in enumerate(chunk_detailed_descriptions, start=1):
                    aggregated_descriptions += f"Folder content subset {idx} description for folder {folder_name}:\n\n{c_str}\n\n"
                compression_idx = 0
                while len(aggregated_descriptions) >= chunk_size:
                    chunks = chunk_str(
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                        str_in=aggregated_descriptions,
                    )
                    with FastShutdownThreadPoolExecutor(
                        max_workers=max_workers
                    ) as executor:
                        num_chunks = len(chunks)
                        futures = {
                            executor.submit(
                                folder_compress_chunks,
                                llm,
                                folder_name,
                                codebase_name,
                                c_str,
                            ): idx
                            for idx, c_str in enumerate(chunks)
                        }
                        # Make sure the original chunk order is preserved.
                        results = []
                        for idx, future in enumerate(
                            concurrent.futures.as_completed(futures.keys())
                        ):
                            res = future.result()
                            if res is not None:
                                print(
                                    f"Processed {idx}/{num_chunks-1} chunks for folder `{folder_name}` "
                                    f"in compression iteration {compression_idx}"
                                )
                                results.append((futures[future], res))
                        chunk_detailed_descriptions = [
                            r for (_idx, r) in sorted(results, key=lambda tup: tup[0])
                        ]
                    aggregated_descriptions = ""
                    for idx, c_str in enumerate(chunk_detailed_descriptions, start=1):
                        aggregated_descriptions += (
                            f"Folder content subset {idx} description for folder {folder_name}:"
                            f"\n\n{c_str}\n\n"
                        )
                    compression_idx += 1
                    if compression_idx >= compression_loop_max_itr:
                        if raise_hard_errors:
                            raise RuntimeError(
                                f"Compression loop max iteration ({compression_loop_max_itr}) "
                                f"reached for folder `{folder_name}`"
                            )
                        else:
                            print(
                                f"Compression loop max iteration ({compression_loop_max_itr}) "
                                f"reached for folder `{folder_name}`"
                            )
                            print(
                                f"WARNING: Compression loop max iteration ({compression_loop_max_itr}) "
                                f"reached for folder `{folder_name}`"
                            )
                            description = "Folder contents too large to process."
                            return _return_with_simple_message(
                                message=description,
                                folder_node=node,
                            )

                print(f"`chunk_detailed_descriptions`: {chunk_detailed_descriptions}")
                data = aggregated_descriptions
            else:
                chunk_detailed_descriptions = []
                for idx, c_str in enumerate(chunks):
                    chunk_detailed_descriptions.append(
                        folder_chunk_description(
                            llm=llm,
                            folder_name=folder_name,
                            codebase_name=codebase_name,
                            description_chunk=c_str,
                        )
                    )
                    print(
                        f"Initial folder child content chunk {idx + 1}/{num_chunks} processed for folder `{folder_name}`"
                    )
                    print(
                        f"Initial folder child content chunk {idx + 1}/{num_chunks} processed for folder `{folder_name}`"
                    )
                # Compression steps, if needed.
                aggregated_descriptions = ""
                for idx, c_str in enumerate(chunk_detailed_descriptions, start=1):
                    aggregated_descriptions += f"Folder content subset {idx} description for folder {folder_name}:\n\n{c_str}\n\n"
                compression_idx = 0
                while len(aggregated_descriptions) >= chunk_size:
                    chunks = chunk_str(
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                        str_in=aggregated_descriptions,
                    )
                    print(
                        f"Compressing {len(chunks)} chunk descriptions for folder `{folder_name}`"
                    )
                    print(
                        f"Compressing {len(chunks)} chunk descriptions for folder `{folder_name}`"
                    )
                    chunk_detailed_descriptions = []
                    for idx, c_str in enumerate(chunks):
                        chunk_detailed_descriptions.append(
                            folder_compress_chunks(
                                llm=llm,
                                folder_name=folder_name,
                                codebase_name=codebase_name,
                                description_chunk=c_str,
                            )
                        )
                        print(
                            f"Compression chunk {idx + 1}/{num_chunks} for compression iteration "
                            f"{compression_idx + 1} processed for folder `{folder_name}`"
                        )
                    aggregated_descriptions = ""
                    for idx, c_str in enumerate(chunk_detailed_descriptions, start=1):
                        aggregated_descriptions += f"Folder content subset {idx} description for folder {folder_name}:\n\n{c_str}\n\n"
                    compression_idx += 1
                    if compression_idx >= compression_loop_max_itr:
                        if raise_hard_errors:
                            raise RuntimeError(
                                f"Compression loop max iteration ({compression_loop_max_itr}) reached for folder `{folder_name}`"
                            )
                        else:
                            print(
                                f"WARNING: Compression loop max iteration ({compression_loop_max_itr}) reached for folder `{folder_name}`"
                            )
                            description = "Folder ontents too large to process."
                            return _return_with_simple_message(
                                message=description,
                                folder_node=node,
                            )
                print(f"`chunk_detailed_descriptions`: {chunk_detailed_descriptions}")
                data = aggregated_descriptions
        else:  # just a single aggregated chunk
            aggregation_state = AggregationState.SINGLE_CHUNK
            data = child_content
    else:  # child list is small enough
        aggregation_state = AggregationState.CHILD_LIST
        data = completed_child_lists

    # Dispatch to the correct single sentence/paragraph generation function depending on the
    # compression/aggregation strategy that was used.
    print(f"Generating final folder content for `{folder_name}` ...")
    match aggregation_state:
        case AggregationState.MANY_CHUNKS:
            single_sentence_fn = folder_single_sentence_from_chunk_descriptions
            single_paragraph_fn = folder_single_paragraph_from_chunk_descriptions
        case AggregationState.SINGLE_CHUNK:
            single_sentence_fn = folder_single_sentence_from_long_descriptions
            single_paragraph_fn = folder_single_paragraph_from_long_descriptions
        case AggregationState.CHILD_LIST:
            single_sentence_fn = folder_single_sentence_from_child_list
            single_paragraph_fn = folder_single_paragraph_from_child_list
        case _:
            raise ValueError(
                f"Unexpected value `{aggregation_state}` for `aggregation_state` for folder processing"
            )
    if use_async:
        with FastShutdownThreadPoolExecutor(max_workers=max_workers) as executor:
            single_sentence_future = executor.submit(
                single_sentence_fn,
                llm,
                folder_name,
                codebase_name,
                data,
            )
            single_paragraph_future = executor.submit(
                single_paragraph_fn,
                llm,
                folder_name,
                codebase_name,
                data,
            )
            short_descriptions = {
                "single_sentence": single_sentence_future.result(),
                "single_paragraph": single_paragraph_future.result(),
            }
    else:
        single_sentence = single_sentence_fn(
            llm=llm,
            folder_name=folder_name,
            codebase_name=codebase_name,
            data=data,
        )
        single_paragraph = single_paragraph_fn(
            llm=llm,
            folder_name=folder_name,
            codebase_name=codebase_name,
            data=data,
        )
        short_descriptions = {
            "single_sentence": single_sentence,
            "single_paragraph": single_paragraph,
        }
    long_description = completed_child_lists

    print(
        f"Short description for `{folder_name}` at `{node.root_rel_path}`:\n{short_descriptions['single_paragraph']}"
    )

    return {
        "short": short_descriptions,
        "long": long_description,
    }
