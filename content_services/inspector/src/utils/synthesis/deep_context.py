import asyncio
from enum import StrEnum
from typing import Self

from aiolimiter import AsyncLimiter
from database.models_v2_enums import ContentKind
from pydantic import BaseModel
from shared.agent.chat_openai_async import ChatOpenAI, OutputConfig
from shared.prompts.structured_prompting import (
    Component,
    Prompt,
)
from utils.dag import FlatTopoFileDiffDag
from utils.update_flow import DiffUpdatable

OPENAI_SEM = asyncio.Semaphore(300)
OPENAI_RATE_LIMITER = AsyncLimiter(100, 1)
CHUNK_SIZE_LIMIT = 96_000


# TODO: Redundant with content in places like `entry_point.py`. Unify.
async def bounded_llm_generate(
    llm: ChatOpenAI,
    system_prompt: str,
    user_prompt: str,
    sem: asyncio.Semaphore,
    rate_limiter: AsyncLimiter,
    output_cfg: OutputConfig = OutputConfig.default(),
) -> str:
    async with sem, rate_limiter:
        return await llm.generate_response(
            system_prompt=system_prompt, user_prompt=user_prompt, output_cfg=output_cfg
        )


class DocUpdateRelevance(StrEnum):
    VeryRelevant = "very_relevant"
    PossiblyRelevant = "possibly_relevant"
    NotRelevant = "not_relevant"


class RelevanceFlag(BaseModel):
    flag: DocUpdateRelevance

    @staticmethod
    def system_prompt(doc_specific_details: Component) -> str:
        identity_preamble = """
You are an expert software engineer and technical writier that specializes in updating existing documents about a software codebase when changes are made to the underlying code.
        """

        deep_context_docs_preamble = """
The kind of document under consideration for being updated is a "deep context document." The specific kind of deep context document is detailed below. But broadly speaking, these documents are intended to be comprehensive and exhaustive on a particular topic, but necessarily high level because they are usually the size of 1 -- 3 pages to cover a large scope such as an entire codebase. Any detail will be specific to the kind of document (e.g., an onboarding guide document may require detailed accounting of file path changes).
        """

        task_description = """
Your job is to review a code diff for a file provided to you and decide if it is significant enough to be considered for updating a particular document. Here are the details on the particular document kind under consideration as well as how to think about content being relevant:
        """

        task_afterword = """
It is important for documentation to mostly stay the same between code revisions _unless_ the changes are significant. Be selective in what you mark as very relevant or possibly relevant, erring on the conservative side (i.e., mark as not relevant if it is not clear).

You will be given the output of `git diff` for a specific file and will respond only with your categorization for the relevance of this file in consideration of updating the target document.
        """

        return (
            Prompt.empty()
            .append(Component(string=identity_preamble))
            .append(Component(string=deep_context_docs_preamble))
            .append(Component(string=task_description))
            .append(doc_specific_details)
            .append(Component(string=task_afterword))
        )


class DeepContextDocKind(StrEnum):
    ARCHITECTURE = "architecture-overview"
    LLM_ONBOARDING = "llm-onboarding-guide"
    # CHANGELOG = "changelog" # TODO: @shane do we want to unify or not?
    BESPOKE = "bespoke"

    # TODO: Can we convert `ContentKind` to `StrEnum` for trivial `.value` transformation?
    def into_content_kind(self) -> ContentKind:
        match self:
            case DeepContextDocKind.ARCHITECTURE:
                return ContentKind.DEEP_CONTEXT_ARCHITECTURE
            case DeepContextDocKind.LLM_ONBOARDING:
                return ContentKind.DEEP_CONTEXT_LLM_ONBOARDING
            case DeepContextDocKind.BESPOKE:
                return ContentKind.DEEP_CONTEXT_BESPOKE
            case _:
                raise ValueError("Unreachable")

    @classmethod
    def from_content_kind(cls, content_kind: ContentKind) -> Self:
        match content_kind:
            case ContentKind.DEEP_CONTEXT_ARCHITECTURE:
                return cls.ARCHITECTURE
            case ContentKind.DEEP_CONTEXT_LLM_ONBOARDING:
                return cls.LLM_ONBOARDING
            case ContentKind.DEEP_CONTEXT_BESPOKE:
                return cls.BESPOKE
            case _:
                raise ValueError(
                    f"Unsupported `ContentKind`: {content_kind} for Deep Context Doc creation"
                )


class DeepContextDoc(DiffUpdatable, BaseModel):
    doc_kind: DeepContextDocKind
    name: str | None
    user_context: dict[str, str] | None
    sources: list[tuple[str, list[str]]]
    config_content: str  # TODO: keep in structured format
    doc_content: str

    @property
    def sections(self) -> list[str]:
        return [s for (s, _) in self.sources]

    async def update_from_diff(self, diff: FlatTopoFileDiffDag) -> Self:
        # TODO:
        # Filter, process, and aggregate on diff nodes.
        # Branch on complexity for update logic.
        # Complete the update and return a new doc.
        # llm = AsyncChatOpenAI(
        #     model="gpt-4o-2024-08-06", temperature=0, request_timeout=500
        # ),
        pass


async def update_deep_context_doc(old_content: str, diff: FlatTopoFileDiffDag) -> str:
    return old_content
