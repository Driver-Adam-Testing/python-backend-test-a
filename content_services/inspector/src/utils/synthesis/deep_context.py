import asyncio
from enum import StrEnum
from typing import Self

from aiolimiter import AsyncLimiter
from database.models_enums import ContentKind
from pydantic import BaseModel
from shared.agent.chat_openai_async import ChatOpenAI, OutputConfig, OutputConfigKind
from shared.chunking.text_splitter import split_text
from shared.prompts.structured_prompting import (
    GENERAL_STE_STYLE_INSTRUCTION,
    Component,
    Prompt,
)
from utils.dag import FlatTopoFileDiffDag, LiteNode
from utils.synthesis.deep_context_prompts import (
    ARCHITECTURE_DOC_DESCRIPTION,
    DEEP_CONTEXT_DOCS_PREAMBLE,
    LLM_ONBOARDING_DOC_DESCRIPTION,
    UPDATER_IDENTITY_PREAMBLE,
)
from utils.update_flow import DiffUpdatable

TAG_MODEL = "gpt-4.1"
UPDATE_SINGLE_SHOT_MODEL = "gpt-4.1"
UPDATE_FEW_SHOT_SEQUENTIAL_MODEL = "gpt-4.1"
UPDATE_MANY_SHOT_CHUNK_MODEL = "gpt-4.1"
UPDATE_MANY_SHOT_AGGREGATE_MODEL = "gpt-5"

OPENAI_SEM = asyncio.Semaphore(300)
OPENAI_RATE_LIMITER = AsyncLimiter(100, 1)
CHUNK_SIZE_LIMIT = 96_000
CHUNK_SIZE_FOR_DIFF_AGGREGATION = 96_000
CHUNK_OVERLAP_FOR_SEQUENTIAL_DIFF_PROCESSING = int(
    CHUNK_SIZE_FOR_DIFF_AGGREGATION * 0.05
)


# TODO: Redundant with content in places like `entry_point.py`. Unify.
# TODO: We should ultimately use this _very carefully_ to be robust and not miss out on critical information in the future.
def _clip_prompt(p: str, chunk_size: int) -> str:
    prompt_chunks = split_text(p, chunk_size=chunk_size, chunk_overlap=0)
    return prompt_chunks[0].text if len(prompt_chunks) > 1 else p


def _combine_diffs(diffs: list[str]) -> str:
    prompt = Prompt.empty()
    for d in diffs:
        prompt.append(Component(string=d))

    return prompt.into_str()


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


class DocUpdateRelevance(StrEnum):
    VeryRelevant = "very_relevant"
    PossiblyRelevant = "possibly_relevant"
    NotRelevant = "not_relevant"


class RelevanceFlag(BaseModel):
    flag: DocUpdateRelevance

    @staticmethod
    def system_prompt(doc_kind: DeepContextDocKind) -> str:
        task_description = Component(
            string="""
Your job is to review a code diff for a file provided to you and decide if it is significant enough to be considered for updating a particular document. Here are the details on the particular document kind under consideration as well as how to think about content being relevant:
            """
        )

        match doc_kind:
            case DeepContextDocKind.LLM_ONBOARDING:
                doc_description = LLM_ONBOARDING_DOC_DESCRIPTION
                tag_descriptions = Component(
                    string="""
**very_relevant**: This means the diff content is highly likely to require updates to an LLM onboarding guide document. For example, it represents a major refactor of major existing functionality, significant new feature development, or major changes to interfaces between components and directory structure. These are just some specific examples, but this category represents any major changes that would be expected to change how you onboard a person or LLM to the codebase.

**possibly_relevant**: This means the diff content may not be at the level of major overhaul but changes the behavior/nature/interface of the codebase enough that it may be important to reflect in the LLM onboarding guide document. Such changes would likely be small to the document but important to accurately reflect the codebase when discussing its contents and navigation. Renaming of files or moving pieces of code around should probably be tagged as possible relevant. Even if it doesn't change functionality, it may be important to update statements about paths/where implementation content is found in the codebase in the onboarding guide.

**not_relevant**: This means the diff content is not important to make updates to an LLM onboarding guide. The code changes may be important (bug fix, retire tech debt, performance improvement, part of new feature development, etc.) in various sense of the word "important" to the development of the codebase, but unlikely to require editing and updating of a top level LLM onboarding guide document. The code diff may be substantial in terms of lines of code changes, etc., but does not rise to the level of being relevant to changing how an onboarding guide is built.
                    """
                )

            case DeepContextDocKind.ARCHITECTURE:
                doc_description = ARCHITECTURE_DOC_DESCRIPTION
                tag_descriptions = Component(
                    string="""
**very_relevant**: This means the diff content is highly likely to require updates to an archiecture overview document. For example: it represents a major refactor of major existing functionality, new feature development significant enough to affect thinking about architecture, or major changes to interfaces between key components. These are just some specific examples, but this category represents any major changes that would be expected to change how you explain the architecture of the codebase.

**possibly_relevant**: This means the diff content may not be at the level of major overhaul but changes the behavior/nature/interface of the codebase enough that it may be important to reflect in the architecture overview document. Such changes would likely be small but important to reflect the architecture accurately. Renaming of files or moving pieces of code around should probably be tagged as possibly relevant. Even if it doesn't change the architecture, it may be important to update statements about paths/where implementation content is found in the codebase in the architecture overview.

**not_relevant**: This means the diff content is not important to make updates to an architecture overview document. The code changes may be important (bug fix, retire tech debt, performance improvement, part of new feature development, etc.) in various senses of the word "important" to the development of the codebase, but unlikely to require editing and updating of a top level architecture document. The code diff may be substantial in terms of lines of code changes, etc., but does not rise the level of being relevant to changing how an architecture overview is explained.
                    """
                )

            case _:
                raise ValueError(
                    f"Relevance tagging in the update flow not supported for doc kind: {doc_kind}"
                )

        task_afterword = Component(
            string="""
It is important for documentation to mostly stay the same between code revisions _unless_ the changes are significant. Be selective in what you mark as very relevant or possibly relevant, erring on the conservative side (i.e., mark as not relevant if it is not clear).

You will be given the output of `git diff` for a specific file and will respond only with your categorization for the relevance of this file in consideration of updating the target document.
            """
        )

        return (
            Prompt.empty()
            .append(UPDATER_IDENTITY_PREAMBLE)
            .append(DEEP_CONTEXT_DOCS_PREAMBLE)
            .append(task_description)
            .append(doc_description)
            .append(tag_descriptions)
            .append(task_afterword)
            .into_str()
        )

    @classmethod
    async def from_llm(
        cls,
        llm: ChatOpenAI,
        root_rel_path: str,
        doc_kind: DeepContextDocKind,
        diff: str,
    ) -> Self:
        system_prompt = cls.system_prompt(doc_kind=doc_kind)
        user_prompt = _clip_prompt(
            p=f"File (`{root_rel_path}`) git diff:\n{diff}", chunk_size=CHUNK_SIZE_LIMIT
        )
        content_raw = await bounded_llm_generate(
            llm=llm,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            sem=OPENAI_SEM,
            rate_limiter=OPENAI_RATE_LIMITER,
            output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
        )
        return cls.parse_raw(content_raw)


# class UpdatedDocument(BaseModel):
#     updated_content: str
#     rationale: str
#
#
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

    @staticmethod
    def system_prompt_single_shot(doc_kind: DeepContextDocKind) -> str:
        match doc_kind:
            case DeepContextDocKind.LLM_ONBOARDING:
                doc_description = LLM_ONBOARDING_DOC_DESCRIPTION
            case DeepContextDocKind.ARCHITECTURE:
                doc_description = ARCHITECTURE_DOC_DESCRIPTION
            case _:
                raise ValueError(
                    f"Unsupported doc kind for one-shot update flow: {doc_kind}"
                )
        task_description = Component(
            string="""
Code diff content deemed relevant to updating the current document has been previously collected and aggregated together. Your job is to take the collected diff content and update the previous version of this deep context document. Here are some further instruction and consideration for updating the document based on the particular kind of document you will be updating:
            """
        )

        task_afterword = Component(
            string="""
It is important for documentation to mostly stay the same between code revisions _unless_ the changes are significant. Be selective in what and how you update the existing document. Make sure to update/replace any content that is outdated or incorrect in view of the new state of the code apparent from the diff content. And if the changes are so significant that the major structure and organization of the document should be significantly altered, make those edits. But generally err on the conservative side and make as few changes to the original document as needed.

You will be given the aggregated diff content of relevant changed files first followed by the target document's previous version content. You will respond only with your updated/edited version of the target document.
            """
        )

        return (
            Prompt.empty()
            .append(UPDATER_IDENTITY_PREAMBLE)
            .append(DEEP_CONTEXT_DOCS_PREAMBLE)
            .append(task_description)
            .append(doc_description)
            .append(task_afterword)
            .append(GENERAL_STE_STYLE_INSTRUCTION)
            .into_str()
        )

    async def _update_from_llm_single_shot(self, combined_diff: str) -> Self:
        llm = (
            ChatOpenAI(
                model=UPDATE_SINGLE_SHOT_MODEL, temperature=0, request_timeout=500
            ),
        )
        system_prompt = type(self).system_prompt_single_shot(doc_kind=self.doc_kind)
        user_prompt = f"**Diff content**:\n\n{combined_diff}\n\n**Previous document version**:\n\n{self.doc_content}"

        content_raw = await bounded_llm_generate(
            llm=llm,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            sem=OPENAI_SEM,
            rate_limiter=OPENAI_RATE_LIMITER,
            output_cfg=OutputConfig.default(),
        )
        # updated_document = UpdatedDocument.parse_raw(content_raw)
        updated_document = content_raw

        return Self(
            doc_kind=self.doc_kind,
            name=self.name,
            user_context=self.user_context,
            sources=self.sources,
            config_content=self.config_content,
            doc_content=updated_document,
        )

    async def _update_from_llm_sequential(self, diff_chunks: list[str]) -> Self:
        llm = ChatOpenAI(
            model=UPDATE_FEW_SHOT_SEQUENTIAL_MODEL, temperature=0, request_timeout=500
        )
        system_prompt = type(self).system_prompt_single_shot(doc_kind=self.doc_kind)

        updated_document = self.doc_content
        for diff in diff_chunks:
            user_prompt = f"**Diff content**:\n\n{diff}\n\n**Previous document version**:\n\n{updated_document}"
            updated_document = await bounded_llm_generate(
                llm=llm,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                sem=OPENAI_SEM,
                rate_limiter=OPENAI_RATE_LIMITER,
                output_cfg=OutputConfig.default(),
            )

        return Self(
            doc_kind=self.doc_kind,
            name=self.name,
            user_context=self.user_context,
            sources=self.sources,
            config_content=self.config_content,
            doc_content=updated_document,
        )

    async def _update_from_llm_scatter_gather(
        relevant_diffs: list[tuple[LiteNode, str]],
    ) -> Self:
        # TODO: Strategy: emit dense descriptions of how to change the doc from each scatter, combine in gather.
        raise NotImplementedError()

    async def update_from_diff(self, diff_collection: FlatTopoFileDiffDag) -> Self:
        # Step 1: Filter files for relevance.
        llm_relevance_tagging = (
            ChatOpenAI(model=TAG_MODEL, temperature=0, request_timeout=500),
        )

        root, tsort_dag = diff_collection
        async with asyncio.TaskGroup() as tg:
            relevance_coros = []
            for node, diff in tsort_dag:
                relevance_coros.append(
                    (
                        node,
                        diff,
                        tg.create_task(
                            RelevanceFlag.from_llm(
                                llm=llm_relevance_tagging,
                                root_rel_path=node.root_rel_path,
                                doc_kind=self.doc_kind,
                                diff=diff,
                            )
                        ),
                    )
                )

        relevance_list = [(n, d, c.result()) for n, d, c in relevance_coros]

        is_relevant_list = [
            (n, d, c)
            for n, d, c in relevance_list
            if c.flag == DocUpdateRelevance.VeryRelevant
            or c.flag == DocUpdateRelevance.PossiblyRelevant
        ]
        is_relevant_diffs = [d for _n, d, _c in is_relevant_list]
        is_relevant_diffs_with_nodes = [(n, d) for n, d, _c in is_relevant_list]

        # If nothing is relevant, return the original document
        # TODO: should this be a deep copy?
        if not is_relevant_diffs:
            return self

        is_relevant_combined_diffs_chunks = split_text(
            text=_combine_diffs(diffs=is_relevant_diffs),
            chunk_size=CHUNK_SIZE_FOR_DIFF_AGGREGATION,
            chunk_overlap=0,
        )

        is_relevant_combined_diff_str_chunks = [
            c.text for c in is_relevant_combined_diffs_chunks
        ]

        # Step 2: Dispatch to LLM update generation based on size of aggregated `git diff` strings.
        match len(is_relevant_combined_diff_str_chunks):
            case 0:
                raise ValueError("Unreachable")
            # If everything fits comfortably in a single context window, single shot it.
            case 1:
                return await self._update_from_llm_single_shot(
                    combined_diff=is_relevant_combined_diff_str_chunks[0]
                )
            # If there are only a few aggregated chunks, do a short sequential processing.
            case n if 2 <= n <= 5:
                # Re-chunk with some overlap to aid sequential procesing.
                chunks_with_minor_overlap = [
                    c.text
                    for c in split_text(
                        text=_combine_diffs(diffs=is_relevant_diffs),
                        chunk_size=CHUNK_SIZE_FOR_DIFF_AGGREGATION,
                        chunk_overlap=CHUNK_OVERLAP_FOR_SEQUENTIAL_DIFF_PROCESSING,
                    )
                ]
                return await self._update_from_llm_sequential(
                    diff_chunks=chunks_with_minor_overlap
                )
            # For very large diffs, use a scatter-gather approach.
            case _:
                return await self._update_from_llm_scatter_gather(
                    relevant_diffs=is_relevant_diffs_with_nodes
                )
