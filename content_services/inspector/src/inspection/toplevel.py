import concurrent.futures
import json
from pathlib import Path
from typing import Any, Optional

from tqdm import tqdm

from utils.dag import NodeKind, LiteNode
from utils.io import (
    get_prompt_template,
)
from utils.llm import chunk_str
from utils.models import ChatOpenAI
from utils.threadpool import FastShutdownThreadPoolExecutor

PARENT_PATH = Path(__file__).parent


def toplevel_chunk_description(
    llm: ChatOpenAI,
    codebase_name: str,
    description_chunk: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH / "prompt_templates/toplevel/chunk_description.txt"
    )
    human_prompt = f"Chunk of content descriptions for codebase `{codebase_name}`:\n\n{description_chunk}"
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_compress_chunks(
    llm: ChatOpenAI,
    codebase_name: str,
    description_chunk: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH / "prompt_templates/toplevel/compress_chunks.txt"
    )
    human_prompt = f"Chunk of module subset descriptions for codebase `{codebase_name}`:\n\n{description_chunk}"
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_long_from_chunk_descriptions(
    llm: ChatOpenAI,
    codebase_name: str,
    data: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH / "prompt_templates/toplevel/long_from_chunk_descriptions.txt"
    )
    human_prompt = data
    human_prompt = ""
    human_prompt += (
        f"Chunk of module subset descriptions for codebase {codebase_name}\n\n"
    )
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_terse_sentence_from_chunk_descriptions(
    llm: ChatOpenAI,
    data: str,
    codebase_name: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/toplevel/terse_sentence_from_chunk_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += (
        f"Chunk of module subset descriptions for codebase {codebase_name}\n\n"
    )
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_single_sentence_from_chunk_descriptions(
    llm: ChatOpenAI,
    data: str,
    codebase_name: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/toplevel/single_sentence_from_chunk_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += (
        f"Chunk of module subset descriptions for codebase {codebase_name}\n\n"
    )
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_single_paragraph_from_chunk_descriptions(
    llm: ChatOpenAI,
    data: str,
    codebase_name: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/toplevel/single_paragraph_from_chunk_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += (
        f"Chunk of module subset descriptions for codebase {codebase_name}\n\n"
    )
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_quickstart_guide_from_chunk_descriptions(
    llm: ChatOpenAI,
    data: str,
    codebase_name: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/toplevel/quickstart_guide_use_from_chunk_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += (
        f"Chunk of module subset descriptions for codebase {codebase_name}\n\n"
    )
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_quickstart_guide_use_from_chunk_descriptions(
    llm: ChatOpenAI,
    data: str,
    codebase_name: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/toplevel/quickstart_guide_use_from_chunk_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += (
        f"Chunk of module subset descriptions for codebase {codebase_name}\n\n"
    )
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_quickstart_guide_dependencies_from_chunk_descriptions(
    llm: ChatOpenAI,
    data: str,
    codebase_name: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/toplevel/quickstart_guide_dependencies_from_chunk_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += (
        f"Chunk of module subset descriptions for codebase {codebase_name}\n\n"
    )
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_quickstart_guide_entry_from_chunk_descriptions(
    llm: ChatOpenAI,
    data: str,
    codebase_name: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/toplevel/quickstart_guide_entry_from_chunk_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += (
        f"Chunk of module subset descriptions for codebase {codebase_name}\n\n"
    )
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_quickstart_guide_getting_started_from_chunk_descriptions(
    llm: ChatOpenAI,
    data: str,
    codebase_name: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/toplevel/quickstart_guide_getting_started_from_chunk_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += (
        f"Chunk of module subset descriptions for codebase {codebase_name}\n\n"
    )
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_user_stories_from_chunk_descriptions(
    llm: ChatOpenAI,
    data: str,
    codebase_name: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/toplevel/user_stories_from_chunk_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += (
        f"Chunk of module subset descriptions for codebase {codebase_name}\n\n"
    )
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_business_logic_from_chunk_descriptions(
    llm: ChatOpenAI,
    data: str,
    codebase_name: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/toplevel/business_logic_from_chunk_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += (
        f"Chunk of module subset descriptions for codebase {codebase_name}\n\n"
    )
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_explore_from_chunk_descriptions(
    llm: ChatOpenAI,
    data: str,
    codebase_name: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH / "prompt_templates/toplevel/explore_from_chunk_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += (
        f"Chunk of module subset descriptions for codebase {codebase_name}\n\n"
    )
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_long_from_long_descriptions(
    llm: ChatOpenAI,
    codebase_name: str,
    data: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH / "prompt_templates/toplevel/long_from_long_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += f"Codebase name: {codebase_name}\n\n"
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_terse_sentence_from_long_descriptions(
    llm: ChatOpenAI, codebase_name: str, data: str
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/toplevel/terse_sentence_from_long_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += f"Codebase name: {codebase_name}\n\n"
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_single_sentence_from_long_descriptions(
    llm: ChatOpenAI, codebase_name: str, data: str
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/toplevel/single_sentence_from_long_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += f"Codebase name: {codebase_name}\n\n"
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_single_paragraph_from_long_descriptions(
    llm: ChatOpenAI, codebase_name: str, data: str
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/toplevel/single_paragraph_from_long_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += f"Codebase name: {codebase_name}\n\n"
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_quickstart_guide_from_long_descriptions(
    llm: ChatOpenAI,
    codebase_name: str,
    data: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/toplevel/quickstart_guide_from_long_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += f"Codebase name: {codebase_name}\n\n"
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_quickstart_guide_use_from_long_descriptions(
    llm: ChatOpenAI,
    codebase_name: str,
    data: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/toplevel/quickstart_guide_use_from_long_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += f"Codebase name: {codebase_name}\n\n"
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_quickstart_guide_dependencies_from_long_descriptions(
    llm: ChatOpenAI,
    codebase_name: str,
    data: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/toplevel/quickstart_guide_dependencies_from_long_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += f"Codebase name: {codebase_name}\n\n"
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_quickstart_guide_entry_from_long_descriptions(
    llm: ChatOpenAI,
    codebase_name: str,
    data: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/toplevel/quickstart_guide_entry_from_long_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += f"Codebase name: {codebase_name}\n\n"
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_quickstart_guide_getting_started_from_long_descriptions(
    llm: ChatOpenAI,
    codebase_name: str,
    data: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/toplevel/quickstart_guide_getting_started_from_long_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += f"Codebase name: {codebase_name}\n\n"
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_user_stories_from_long_descriptions(
    llm: ChatOpenAI,
    codebase_name: str,
    data: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/toplevel/user_stories_from_long_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += f"Codebase name: {codebase_name}\n\n"
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_business_logic_from_long_descriptions(
    llm: ChatOpenAI,
    codebase_name: str,
    data: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH
        / "prompt_templates/toplevel/business_logic_from_long_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += f"Codebase name: {codebase_name}\n\n"
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def toplevel_explore_from_long_descriptions(
    llm: ChatOpenAI,
    codebase_name: str,
    data: str,
) -> str:
    system_prompt = get_prompt_template(
        PARENT_PATH / "prompt_templates/toplevel/explore_from_long_descriptions.txt"
    )
    human_prompt = ""
    human_prompt += f"Codebase name: {codebase_name}\n\n"
    human_prompt += data
    return llm.generate_response(system_prompt, human_prompt)


def comprehend_codebase_top_down(
    llm: ChatOpenAI,
    docs: dict[LiteNode, dict[str, Any]],
    codebase_name: str,
    chunk_size: int,
    chunk_overlap: int,
    max_workers: int,
    include_exploratory_generation: bool,
    compression_loop_max_itr: int,
    # to_disk_dir: Optional[str] = None,
    # resume: bool = False,
) -> dict[str, Any]:
    # try:
    #     ir = json.loads(
    #         get_source_file(f=f"{to_disk_dir}/state/toplevel_intermediate.json")
    #     )
    #     aggregation_state, data = ir
    # except Exception as _exc:  # noqa: F841
    #     aggregation_state, data = None, None
    # if resume and aggregation_state is not None and data is not None:
    #     pass
    # else:
    print(f"Aggregating and incorporating module info for codebase `{codebase_name}`")
    codebase_content = ""
    for node in docs:
        if node.kind == NodeKind.FILE:
            codebase_content += (f"File `{node.root_rel_path.name}` at `{node.root_rel_path}` "
                                 f"description:\n\n{docs[node]['long']}\n\n")
        elif node.kind == NodeKind.SUB_FOLDER or node.kind == NodeKind.ROOT_FOLDER:
            codebase_content += (f"Folder `{node.root_rel_path.name}` at `{node.root_rel_path}` "
                                 f"description:\n\n{docs[node]['short']['single_paragraph']}\n\n")
        else:
            raise Exception("Unreachable")

    # write_to_disk(
    #     json.dumps({"codebase_content": codebase_content}),
    #     f"{to_disk_dir}/state/codebase_content.json",
    # )
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
                            f"Processed {idx}/{num_chunks-1} initial top-level chunks"
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
        # write_to_disk(
        #     json.dumps({"aggregated_descriptions": aggregated_descriptions}),
        #     f"{to_disk_dir}/state/aggregated_descriptions_itr_{compression_idx}.json",
        # )
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
                                f"Processed {idx}/{num_chunks-1} chunks for top-level content in compression iteration {compression_idx}"
                            )
                            results.append((futures[future], res))
                        pbar.update(1)
                chunk_detailed_descriptions = [
                    r for (_idx, r) in sorted(results, key=lambda tup: tup[0])
                ]
            aggregated_descriptions = ""
            for idx, c in enumerate(chunk_detailed_descriptions, start=1):
                aggregated_descriptions += f"Content subset {idx} description for codebase {codebase_name}:\n\n{c}\n\n"
            # write_to_disk(
            #     json.dumps({"aggregated_descriptions": aggregated_descriptions}),
            #     f"{to_disk_dir}/state/aggregated_descriptions_itr_{compression_idx}.json",
            # )
            compression_idx += 1

        print(f"`chunk_detailed_descriptions`: {chunk_detailed_descriptions}")
        aggregation_state = "chunks"
        data = aggregated_descriptions
        ir = [aggregation_state, data]
        # write_to_disk(json.dumps(ir), f"{to_disk_dir}/state/intermediate2.json")
    else:
        aggregation_state = "no_chunks"
        data = codebase_content
        ir = [aggregation_state, data]
        # write_to_disk(json.dumps(ir), f"{to_disk_dir}/state/toplevel_intermediate.json")

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
            quickstart_use_future = executor.submit(
                toplevel_quickstart_guide_use_from_chunk_descriptions,
                llm,
                data,
                codebase_name,
            )
            quickstart_dependencies_future = executor.submit(
                toplevel_quickstart_guide_dependencies_from_chunk_descriptions,
                llm,
                data,
                codebase_name,
            )
            quickstart_entry_future = executor.submit(
                toplevel_quickstart_guide_entry_from_chunk_descriptions,
                llm,
                data,
                codebase_name,
            )
            quickstart_getting_started_future = executor.submit(
                toplevel_quickstart_guide_getting_started_from_chunk_descriptions,
                llm,
                data,
                codebase_name,
            )
            user_stories_future = executor.submit(
                toplevel_user_stories_from_chunk_descriptions,
                llm,
                data,
                codebase_name,
            )
            business_logic_future = executor.submit(
                toplevel_business_logic_from_chunk_descriptions,
                llm,
                data,
                codebase_name,
            )
            if include_exploratory_generation:
                explore_future = executor.submit(
                    toplevel_explore_from_chunk_descriptions,
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
            quickstart_use_future = executor.submit(
                toplevel_quickstart_guide_use_from_long_descriptions,
                llm,
                codebase_name,
                data,
            )
            quickstart_dependencies_future = executor.submit(
                toplevel_quickstart_guide_dependencies_from_long_descriptions,
                llm,
                codebase_name,
                data,
            )
            quickstart_entry_future = executor.submit(
                toplevel_quickstart_guide_entry_from_long_descriptions,
                llm,
                codebase_name,
                data,
            )
            quickstart_getting_started_future = executor.submit(
                toplevel_quickstart_guide_getting_started_from_long_descriptions,
                llm,
                codebase_name,
                data,
            )
            user_stories_future = executor.submit(
                toplevel_user_stories_from_long_descriptions,
                llm,
                codebase_name,
                data,
            )
            business_logic_future = executor.submit(
                toplevel_business_logic_from_long_descriptions,
                llm,
                codebase_name,
                data,
            )
            if include_exploratory_generation:
                explore_future = executor.submit(
                    toplevel_explore_from_long_descriptions,
                    llm,
                    codebase_name,
                    data,
                )

        long = long_future.result()
        terse_sentence = terse_sentence_future.result()
        single_sentence = single_sentence_future.result()
        single_paragraph = single_paragraph_future.result()
        quickstart_use = quickstart_use_future.result()
        quickstart_dependencies = quickstart_dependencies_future.result()
        quickstart_entry = quickstart_entry_future.result()
        quickstart_getting_started = quickstart_getting_started_future.result()
        architecture = ""
        user_stories = user_stories_future.result()
        business_logic = business_logic_future.result()
        explore = explore_future.result() if include_exploratory_generation else ""

    short_descriptions = {
        "terse_sentence": terse_sentence,
        "single_sentence": single_sentence,
        "single_paragraph": single_paragraph,
    }
    quickstart = {
        "use": quickstart_use,
        "dependencies": quickstart_dependencies,
        "entry": quickstart_entry,
        "getting_started": quickstart_getting_started,
    }
    print(f"Codebase short description:\n{short_descriptions['single_paragraph']}")

    # if to_disk_dir is not None:
    #     write_to_disk(
    #         data=data,
    #         file=f"{to_disk_dir}/toplevel/{codebase_name}/aggregated_codebase_description.txt",
    #     )
    #     write_to_disk(
    #         data=short_descriptions["terse_sentence"],
    #         file=f"{to_disk_dir}/toplevel/{codebase_name}/terse_sentence_description.txt",
    #     )
    #     write_to_disk(
    #         data=short_descriptions["single_sentence"],
    #         file=f"{to_disk_dir}/toplevel/{codebase_name}/single_sentence_description.txt",
    #     )
    #     write_to_disk(
    #         data=short_descriptions["single_paragraph"],
    #         file=f"{to_disk_dir}/toplevel/{codebase_name}/single_paragraph_description.txt",
    #     )
    #     write_to_disk(
    #         data=long,
    #         file=f"{to_disk_dir}/toplevel/{codebase_name}/long_description.txt",
    #     )
    #     write_to_disk(
    #         data=quickstart["use"],
    #         file=f"{to_disk_dir}/toplevel/{codebase_name}/quickstart_use.txt",
    #     )
    #     write_to_disk(
    #         data=quickstart["dependencies"],
    #         file=f"{to_disk_dir}/toplevel/{codebase_name}/quickstart_dependencies.txt",
    #     )
    #     write_to_disk(
    #         data=quickstart["entry"],
    #         file=f"{to_disk_dir}/toplevel/{codebase_name}/quickstart_entry.txt",
    #     )
    #     write_to_disk(
    #         data=quickstart["getting_started"],
    #         file=f"{to_disk_dir}/toplevel/{codebase_name}/quickstart_getting_started.txt",
    #     )
    #     write_to_disk(
    #         data=architecture,
    #         file=f"{to_disk_dir}/toplevel/{codebase_name}/architecture.txt",
    #     )
    #     write_to_disk(
    #         data=user_stories,
    #         file=f"{to_disk_dir}/toplevel/{codebase_name}/user_stories.txt",
    #     )
    #     write_to_disk(
    #         data=business_logic,
    #         file=f"{to_disk_dir}/toplevel/{codebase_name}/business_logic.txt",
    #     )
    #     write_to_disk(
    #         data=explore,
    #         file=f"{to_disk_dir}/toplevel/{codebase_name}/explore.txt",
    #     )

    return {
        "aggregated_description": data,
        "short": short_descriptions,
        "long": long,
        "quickstart": quickstart,
        "architecture": architecture,
        "user_stories": user_stories,
        "business_logic": business_logic,
        "explore": explore,
    }
