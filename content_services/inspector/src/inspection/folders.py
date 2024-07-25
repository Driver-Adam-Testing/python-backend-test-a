import concurrent.futures
from dataclasses import dataclass
from pathlib import Path

from utils.dag import LiteNode, NodeKind
from utils.io import get_prompt_template
from utils.llm import chunk_str
from utils.models import ChatOpenAI
from utils.threadpool import FastShutdownThreadPoolExecutor

PARENT_PATH = Path(__file__).parent


@dataclass(frozen=True)
class ContentDocs:
    docs: dict[str, any]


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
    child_content: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH / "prompt_templates/folders/long_from_long_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += f"Folder `{folder_name}` in codebase `{codebase_name}` content:\n\n{child_content}\n\n"
    return llm.generate_response(system_prompt, human_prompt)


def folder_single_sentence_from_long_descriptions(
    llm: ChatOpenAI,
    folder_name: str,
    codebase_name: str,
    child_content: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/folders/single_sentence_from_long_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += f"Folder `{folder_name}` in codebase `{codebase_name}` content:\n\n{child_content}\n\n"
    return llm.generate_response(system_prompt, human_prompt)


def folder_single_paragraph_from_long_descriptions(
    llm: ChatOpenAI,
    folder_name: str,
    codebase_name: str,
    child_content: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/folders/single_paragraph_from_long_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += f"Folder `{folder_name}` in codebase `{codebase_name}` content:\n\n{child_content}\n\n"
    return llm.generate_response(system_prompt, human_prompt)


# def _write_folder_content_to_disk(
#     dir: str,
#     file_node: Node,
#     folder_content_short: dict[str, str],
#     folder_content_long: str,
# ) -> None:
#     if file_node.kind is not NodeKind.ROOT_FOLDER:
#         write_to_disk(
#             data=folder_content_short["single_sentence"],
#             file=f"{dir}/short_descriptions/{file_node.path_rel_root}_single_sentence.txt",
#         )
#         write_to_disk(
#             data=folder_content_short["single_paragraph"],
#             file=f"{dir}/short_descriptions/{file_node.path_rel_root}_single_paragraph.txt",
#         )
#         write_to_disk(
#             data=folder_content_long,
#             file=f"{dir}/long_descriptions/{file_node.path_rel_root}.txt",
#         )
#     else:
#         write_to_disk(
#             data=folder_content_short["single_sentence"],
#             file=f"{dir}/short_descriptions/{file_folder_name}_single_sentence.txt",
#         )
#         write_to_disk(
#             data=folder_content_short["single_paragraph"],
#             file=f"{dir}/short_descriptions/{file_folder_name}_single_paragraph.txt",
#         )
#         write_to_disk(
#             data=folder_content_long,
#             file=f"{dir}/long_descriptions/{file_folder_name}.txt",
#         )


# def _return_with_simple_message(
#     message: str, file_node: Node, file_content: str, to_disk_dir: Optional[str]
# ) -> dict[str, any]:
#     if to_disk_dir is not None:
#         _write_file_content_to_disk(
#             dir=to_disk_dir,
#             file_node=file_node,
#             chunk_descr=[message],
#             file_content_short={
#                 "single_sentence": message,
#                 "single_paragraph": message,
#             },
#             file_content_long=message,
#             file_content_sys="",
#             file_content_code=file_content,
#         )
#     return {
#         "chunk_descriptions": message,
#         "short": {
#             "single_sentence": message,
#             "single_paragraph": message,
#         },
#         "long": message,
#         "architecture": "",
#     }
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

    print(f"Aggregating and incorporating child info for folder `{folder_name}`")
    child_content = ""
    for k, v in child_nodes_to_docs.items():
        entity = "File" if k.kind == NodeKind.FILE else "Folder"
        long = v["long"]
        child_content += f"{entity} `{k.root_rel_path.name}` description:\n\n{long}\n\n"
    chunks: list[str] = chunk_str(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, str_in=child_content
    )
    num_chunks = len(chunks)
    # TODO: Consider parity with file content generation where there is a
    # TODO: check against a max number of chunks.
    if len(chunks) > 1:
        print(f"Number of initial chunks for folder `{folder_name}`: {num_chunks}")
        print(f"Processing {len(chunks)} chunks for folder `{folder_name}` ...")
        if use_async:
            with FastShutdownThreadPoolExecutor(max_workers=max_workers) as executor:
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
            aggregation_state = "chunks"
            data = aggregated_descriptions
        else:
            chunk_detailed_descriptions = []
            num_chunks = len(chunks)
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
            aggregation_state = "chunks"
            data = aggregated_descriptions

    else:
        aggregation_state = "no_chunks"
        data = child_content

    # TODO: Clean up and remove redundant and unused IRs below.
    child_single_sentence_descriptions = {
        k: v["short"]["single_sentence"] for k, v in child_nodes_to_docs.items()
    }
    child_folder_list = ""
    child_file_list = ""
    for k, v in child_single_sentence_descriptions.items():
        if k.kind == NodeKind.FILE:
            child_file_list += f"- **{k.root_rel_path.name}**: {v}\n"
        # TODO: Careful in assuming non-files are folders.
        else:
            child_folder_list += f"- **{k.root_rel_path.name}**: {v}\n"

    if child_folder_list:
        folder_prefix = "## Folders\n"
        child_folder_list_ordered = folder_item_priority_ordering(
            llm=llm, raw_list_str=f"{folder_prefix}{child_folder_list}"
        )
    else:
        child_folder_list_ordered = ""

    if child_file_list:
        file_prefix = "## Files\n"
        child_file_list_ordered = folder_item_priority_ordering(
            llm=llm, raw_list_str=f"{file_prefix}{child_file_list}"
        )
    else:
        child_file_list_ordered = ""

    child_list = f"{child_folder_list_ordered}\n{child_file_list_ordered}"

    print(f"Generating final folder content for `{folder_name}` ...")
    if use_async:
        with FastShutdownThreadPoolExecutor(max_workers=max_workers) as executor:
            if aggregation_state == "chunks":
                long_future = executor.submit(
                    folder_long_from_chunk_descriptions,
                    llm,
                    folder_name,
                    codebase_name,
                    data,
                )
                single_sentence_future = executor.submit(
                    folder_single_sentence_from_chunk_descriptions,
                    llm,
                    folder_name,
                    codebase_name,
                    data,
                )
                single_paragraph_future = executor.submit(
                    folder_single_paragraph_from_chunk_descriptions,
                    llm,
                    folder_name,
                    codebase_name,
                    data,
                )
            else:
                long_future = executor.submit(
                    folder_long_from_long_descriptions,
                    llm,
                    folder_name,
                    codebase_name,
                    data,
                )
                single_sentence_future = executor.submit(
                    folder_single_sentence_from_long_descriptions,
                    llm,
                    folder_name,
                    codebase_name,
                    data,
                )
                single_paragraph_future = executor.submit(
                    folder_single_paragraph_from_long_descriptions,
                    llm,
                    folder_name,
                    codebase_name,
                    data,
                )
            long_description = long_future.result()
            short_descriptions = {
                "single_sentence": single_sentence_future.result(),
                "single_paragraph": single_paragraph_future.result(),
            }
    else:
        if aggregation_state == "chunks":
            long = folder_long_from_chunk_descriptions(
                llm=llm,
                folder_name=folder_name,
                codebase_name=codebase_name,
                data=data,
            )
            single_sentence = folder_single_sentence_from_chunk_descriptions(
                llm=llm,
                folder_name=folder_name,
                codebase_name=codebase_name,
                data=data,
            )
            single_paragraph = folder_single_paragraph_from_chunk_descriptions(
                llm=llm,
                folder_name=folder_name,
                codebase_name=codebase_name,
                data=data,
            )
        else:
            long = folder_long_from_long_descriptions(
                llm=llm,
                folder_name=folder_name,
                codebase_name=codebase_name,
                child_content=data,
            )
            single_sentence = folder_single_sentence_from_long_descriptions(
                llm=llm,
                folder_name=folder_name,
                codebase_name=codebase_name,
                child_content=data,
            )
            single_paragraph = folder_single_paragraph_from_long_descriptions(
                llm=llm,
                folder_name=folder_name,
                codebase_name=codebase_name,
                child_content=data,
            )
        long_description = long
        short_descriptions = {
            "single_sentence": single_sentence,
            "single_paragraph": single_paragraph,
        }

    print(
        f"Short description for `{folder_name}` at `{node.root_rel_path}`:\n{short_descriptions['single_paragraph']}"
    )
    # if to_disk_dir is not None:
    #     _write_folder_content_to_disk(
    #         dir=to_disk_dir,
    #         file_node=node,
    #         folder_content_short=short_descriptions,
    #         folder_content_long=long_description,
    #     )

    # TODO: Replace this hacked overwrite of `long_description`.
    long_description = child_list
    return {
        "short": short_descriptions,
        "long": long_description,
    }
