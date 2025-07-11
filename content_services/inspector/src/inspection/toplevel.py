import concurrent.futures
from pathlib import Path
from typing import Any, Self

from pydantic import BaseModel
from shared.chunking.text_splitter import split_text
from shared.prompts.structured_prompting import (
    GENERAL_STE_STYLE_INSTRUCTION,
    NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_NODES,
    TERSE_TWITTER_SINGLE_SENTENCE_STYLE_INSTRUCTION,
    Component,
    Prompt,
)
from tqdm import tqdm
from utils.dag import LiteNode, NodeKind
from utils.io import (
    get_prompt_template,
)
from utils.llm import chunk_str
from utils.models import ChatOpenAI, OutputConfig, OutputConfigKind
from utils.threadpool import FastShutdownThreadPoolExecutor

PARENT_PATH = Path(__file__).parent


class CodebaseKindScore(BaseModel):
    sdk: float
    lib: float
    web_frontend: float
    web_backend: float
    desktop: float
    mobile: float
    embedded: float
    data_pipeline: float
    devops: float
    game: float
    enterprise: float
    academic: float
    algorithm: float
    utility: float
    educational: float

    @staticmethod
    def system_prompt() -> str:
        return """
You are an expert engineer well-versed in the many kinds of different software and codebases that exist.

Your job is to generate a relevance score between 0 and 1 for each tag from the finite set of tags applicable to a software codebase. A higher score means a tag is more relevant or applicable to the software codebase under review. The tags are not mutually exclusive. There may be multiple tags highly relevant for a given codebase or relatively few or even only a single one. It all depends on the context and complexity of the codebase. If a tag is not relevant at all to a codebase, give it a score of zero.

Others will review your scores for various signaling and documentation goals such as identifying the single most important/relevant tag and/or documenting the top 3 tags that pertain to a codebase for at-a-glance context. Therefore, your scoring should provide information about how relevant each tag is to the codebase under review in isolation but also in a relative sense with respect to the other tags.

For example, both the "devops" and "enterprise" tags may be correct for a codebase containing core CI/CD code or scripts, but in this context, the codebase overwhelmingly exists as core DevOps functionality and thus the "devops" category should receive a higher score than the "enterprise" tag. When multiple tags are highly relevant for the same codebase, they should all be scored highly (e.g., "lib" and "sdk" will likely often both be relevant), but with not exactly the same score.

Information for the codebase will be provided to you as a list of folder contents. For each folder in the codebase, the path of the folder will be given to you followed by an exhaustive list of every child fild/folder for the given folder, along with a short single sentence description of the content associated with that child (file or folder). Because all children for each folder are listed and information for all folders is provided, you will be given information exhaustively about every file/folder in the codebase. Use this information to make your quantiative scoring decisions.

Here is the list of tags that you will provide relevance scores for. I have given a brief description for each one as a guide for you when determining your relevance scores:

{
   "sdk": Implements a software development kit (SDK) -- a collection of tools for developers to use to build applications for a specific platform or framework.
   "lib": A library designed to be used by/integrated with by other developers in building applications.
   "web_frontend": A frontend web application.
   "web_backend": A backend web application or service with HTTP endpoints to support an application programming interface (API).
   "desktop": Standalone application, with some form of GUI, deployed as a native desktop application.
   "mobile": An application deployed on a mobile device, such as iOS or Android.
   "embedded": Lower level embedded software or mixed HW/SW code.
   "data_pipeline": ETL, analytics, or other data processing system.
   "devops": DevOps or infrastructure code for deployment, CI/CD, monitoring, cloud, or other infrastructure management.
   "game": Interactive game or entertainment software.
   "enterprise": Business applications for the enterprise such as an ERP system.
   "academic": Experimental, research, or academic code.
   "algorithm": Heavy computational, numeric, or algorithm implementation code.
   "utility": Provides utility functionality such as a command line program.
   "educational": Primary purpose is educational or to provide examples.
}
""".strip()

    @classmethod
    def from_llm(
        cls,
        llm: ChatOpenAI,
        docs: dict[LiteNode, dict[str, Any]],
    ) -> Self:
        user_prompt_structured = Prompt.empty()
        for node, ir_data in docs.items():
            match node.kind:
                case NodeKind.ROOT_FOLDER:
                    prefix = "Codebase root folder"
                    content = ir_data["long"]
                case NodeKind.SUB_FOLDER:
                    prefix = "Subfolder"
                    content = ir_data["long"]
                case NodeKind.FILE:
                    continue
                case _:
                    raise ValueError("Unreachable")
            user_prompt_structured.append(
                Component(
                    string=f"{prefix} (`{node.root_rel_path}`) decription:\n{content}"
                )
            )
        user_prompt = user_prompt_structured.into_str()
        user_prompt_chunks = split_text(user_prompt, chunk_size=96_000, chunk_overlap=0)
        if len(user_prompt_chunks) > 1:
            user_prompt = user_prompt_chunks[0].text
        content_raw = llm.generate_response(
            system_prompt=cls.system_prompt(),
            user_prompt=user_prompt,
            output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
        )
        return cls.parse_raw(content_raw)

    def sorted_list(self) -> list[tuple[str, float]]:
        return sorted(
            self.model_dump().items(),
            key=lambda tup: tup[1],
            reverse=True,
        )

    def take(self, n: int) -> list[tuple[str, float]]:
        return self.sorted_list()[:n]

    def top(self) -> tuple[str, float]:
        return self.take(1)[0]


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
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_NODES)
        .append(TERSE_TWITTER_SINGLE_SENTENCE_STYLE_INSTRUCTION)
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
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_NODES)
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
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_NODES)
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
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str()
    )
    user_prompt = (
        Prompt.empty()
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_NODES)
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
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_NODES)
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
        .append(GENERAL_STE_STYLE_INSTRUCTION)
        .into_str()
    )
    user_prompt = (
        Prompt.empty()
        .append(NO_RESTATEMENT_STYLE_INSTRUCTION_FOR_NODES)
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

    codebase_scores = CodebaseKindScore.from_llm(llm=llm, docs=docs)
    print(f"Codebase kind scores:\n\n{codebase_scores.sorted_list()}")
    # top4 = [kind for kind, _ in codebase_scores.take(4)]
    # terse_sentence = f"[{top4[0]}] {terse_sentence}"
    terse_sentence = ""
    sorted_scores = codebase_scores.sorted_list()
    for kind, score in sorted_scores[:-1]:
        terse_sentence += f"{kind}[{score}], "
    terse_sentence += f"{sorted_scores[-1][0]}[{sorted_scores[-1][1]}]"

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
