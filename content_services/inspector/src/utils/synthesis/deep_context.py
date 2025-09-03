from enum import StrEnum
from typing import Self

from database.models_enums import ContentKind
from pydantic import BaseModel


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


class DeepContextDoc(BaseModel):
    doc_kind: DeepContextDocKind
    name: str | None
    user_context: dict[str, str] | None
    sources: list[tuple[str, list[str]]]
    config_content: str  # TODO: keep in structured format
    doc_content: str

    @property
    def sections(self) -> list[str]:
        return [s for (s, _) in self.sources]
