from abc import ABC, abstractclassmethod, abstractmethod
from collections.abc import Callable
from functools import cached_property
from typing import Any, Self

from pydantic import BaseModel
from shared.chunking.text_splitter import split_text
from shared.prompts.structured_prompting import (
    Component,
    Prompt,
)
from utils.dag import LiteNode, NodeKind


class Scorable(BaseModel, ABC):
    @abstractclassmethod
    def tag_descriptions() -> dict[str, str]:
        pass

    @abstractclassmethod
    def system_prompt(cls) -> str:
        pass

    @abstractclassmethod
    def from_llm(cls) -> Self:
        pass

    @abstractmethod
    def to_tag_and_score_pairs(self) -> list[tuple[str, float]]:
        pass

    @cached_property
    def sorted_list(self) -> list[tuple[str, float]]:
        return sorted(
            self.to_tag_and_score_pairs(),
            key=lambda tup: tup[1],
            reverse=True,
        )

    def take(
        self, n: int, pred: Callable[[tuple[str, float]], bool] | None = None
    ) -> list[tuple[str, float]]:
        if pred is None:
            return self.sorted_list[:n]
        else:
            return [el for el in self.sorted_list if pred(el)][:n]

    def top(self) -> tuple[str, float]:
        return self.take(1)[0]


CODEBASE_SCORING_PROMPT_TEMPLATE = """
You are an expert engineer well-versed in the many kinds of different software and codebases that exist.

Your job is to generate a relevance score between 0 and 1 for each tag from the finite set of tags applicable to a software codebase. A higher score means a tag is more relevant or applicable to the software codebase under review. The tags are not mutually exclusive. There may be multiple tags highly relevant for a given codebase or relatively few or even only a single one. It all depends on the context and complexity of the codebase. If a tag is not relevant at all to a codebase, give it a score of zero.

Others will review your scores for various signaling and documentation goals such as identifying the single most important/relevant tag and/or documenting the top 3 tags that pertain to a codebase for at-a-glance context. Therefore, your scoring should provide information about how relevant each tag is to the codebase under review in isolation but also in a relative sense with respect to the other tags.

Information for the codebase will be provided to you as a list of folder contents. For each folder in the codebase, the path of the folder will be given to you followed by an exhaustive list of every child fild/folder for the given folder, along with a short single sentence description of the content associated with that child (file or folder). Because all children for each folder are listed and information for all folders is provided, you will be given information exhaustively about every file/folder in the codebase. Use this information to make your quantiative scoring decisions.

{specific_context}

Here is the list of tags that you will provide relevance scores for. I have given a brief description for each one as a guide for you when determining your relevance scores:

{tag_descriptions}
"""


def build_scoring_user_prompt_from_docs(docs: dict[LiteNode, dict[str, Any]]) -> str:
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

    return user_prompt
