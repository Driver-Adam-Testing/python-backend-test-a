from typing import Any, Self

from shared.prompts.structured_prompting import (
    Component,
    Prompt,
)
from utils.dag import LiteNode
from utils.models import ChatOpenAI, OutputConfig, OutputConfigKind
from utils.tags.scoring import (
    CODEBASE_SCORING_PROMPT_TEMPLATE,
    Scorable,
    build_scoring_user_prompt_from_docs,
)

KIND_MAP = {
    "sdk": "Implements a software development kit (SDK) -- a collection of tools for developers to use to build applications for a specific platform or framework.",
    "lib": "A library designed to be imported and used by other developers in building other programs but not used as a standalone executable or application.",
    "application": "An application or executable intended to be executed as a program and directly serve users. Cf., a library to be integrated into another program or a systems program intended to provide services to other programs. E.g., web application, desktop application, mobile application.",
    "service": "A standalone networked service or daemon, such as a microservice, background daemon, or async job worker.",
    "api": "A codebase whose primary purpose is to define, implement, or expose a formal application programming interface (API) — including REST, GraphQL, gRPC, or language-native interfaces — for use by other software systems or developers.",
    "data_pipeline": "ETL, analytics, or other data processing system.",
    "devops": "DevOps or infrastructure code for deployment, CI/CD, monitoring, cloud, or other infrastructure management.",
    "algorithm": "Heavy computational, numeric, or algorithm implementation code.",
    "cli": "Provides a command line interface utility or application.",
}


DOMAIN_MAP = {
    "embedded": "Lower level embedded software or mixed HW/SW code. E.g.: embedded software libraries, firmware, drivers, RTL code.",
    "web": "Implements part or the whole of a web application.",
    "enterprise": "Business applications for the enterprise such as an ERP system.",
    "game": "Interactive game or entertainment software.",
    "finance": "Code to serve finance-related applications, such as banking and trading.",
    "industrial": "Manufacturing, robotics, and automation.",
    "healthcare": "Applications in medical technologies or regulated health systems.",
    "scientific": "Code used for computational science or numerical simulations.",
    "cloud": "Software directly targeting cloud platforms or cloud-native systems.",
    "security": "Security tools, infosec (e.g., scanning, authentication, identity, threat detection), or systems in cryptography.",
    "desktop": "Standalone application, with some form of UI, deployed as a native desktop application.",
    "mobile": "An application deployed on a mobile device, such as iOS or Android.",
    "academic": "Experimental, research, or academic code.",
    "educational": "Primary purpose is educational or to provide examples.",
    "systems": "Systems software -- low-level or core operational software and which is often intended to provide services to other programs. E.g.: operating systems, compilers.",
}


AUDIENCE_MAP = {
    "internal_user": "Internal tools for non-developer employees (such as Sales, Support, Operations). E.g.: Internal CRM dashbord.",
    "internal_dev": "Tools used by internal developers to build, test, deploy, or operate applications. E.g.: Core product internals or CI/CD pipeline scripts.",
    "end_user": "Customer-facing applications intended for end users. E.g.: Mobile app for end users.",
    "end_dev": "SDKs, APIs, or CLIs used by developers outside the organization. E.g.: Open-source Python SDK.",
    "system": "Codebases that are consumed or executed by systems rather than human users (e.g., telemetry agents, embedded firmware). E.g.: Embedded telemetry daemon.",
    "researcher": "Tools or code intended for internal or external researchers or data scientists.",
}


class CodebaseKindScores(Scorable):
    sdk: float
    lib: float
    application: float
    service: float
    api: float
    data_pipeline: float
    devops: float
    algorithm: float
    cli: float

    @classmethod
    def tag_descriptions(cls) -> dict[str, str]:
        assert set(cls.model_fields.keys()) == set(KIND_MAP.keys())
        return KIND_MAP

    @classmethod
    def system_prompt(cls) -> str:
        specific_context = """
In the case that multiple tags are relevant, it is important to score them all with high values but also differentiate based on the most to least relevant in context. For example, both the "sdk" and "lib" tags may be correct for a codebase implementing a sizeable, powerful, and well-known SDK, with various functionality available as a library to import into another application. But in this context, the SDK nature is most important and thus the "sdk" category should receive a higher score than the "lib" tag.
"""
        tag_descriptions_map = cls.tag_descriptions()
        tag_descriptions_structured = Prompt.empty()
        for k, v in tag_descriptions_map.items():
            tag_descriptions_structured.append(f"{k}: {v}")

        return (
            Prompt.empty()
            .append(
                Component(
                    string=CODEBASE_SCORING_PROMPT_TEMPLATE.format(
                        specific_context=specific_context,
                        tag_descriptions=tag_descriptions_structured.into_str(sep="\n"),
                    )
                )
            )
            .into_str()
        )

    def to_tag_and_score_pairs(self) -> list[tuple[str, float]]:
        return self.model_dump().items()

    @classmethod
    def from_llm(
        cls,
        llm: ChatOpenAI,
        docs: dict[LiteNode, dict[str, Any]],
    ) -> Self:
        user_prompt = build_scoring_user_prompt_from_docs(docs=docs)
        content_raw = llm.generate_response(
            system_prompt=cls.system_prompt(),
            user_prompt=user_prompt,
            output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
        )
        return cls.parse_raw(content_raw)


class CodebaseDomainScores(Scorable):
    embedded: float
    web: float
    enterprise: float
    game: float
    finance: float
    industrial: float
    healthcare: float
    scientific: float
    cloud: float
    security: float
    desktop: float
    mobile: float
    academic: float
    educational: float
    systems: float

    @classmethod
    def tag_descriptions(cls) -> dict[str, str]:
        assert set(cls.model_fields.keys()) == set(DOMAIN_MAP.keys())
        return DOMAIN_MAP

    @classmethod
    def system_prompt(cls) -> str:
        specific_context = """
In the case that multiple tags are relevant, it is important to score them all with high values but also differentiate based on the most to least relevant in context. For example, both the "finance" and "mobile" tags may be correct for a codebase containing a banking app used on a smartphone. In this context, finance app is the most specific and functional descriptor and thus "finance" category should receive a higher score than the "mobile" tag, but both should be high.
"""
        tag_descriptions_map = cls.tag_descriptions()
        tag_descriptions_structured = Prompt.empty()
        for k, v in tag_descriptions_map.items():
            tag_descriptions_structured.append(f"{k}: {v}")

        return (
            Prompt.empty()
            .append(
                Component(
                    string=CODEBASE_SCORING_PROMPT_TEMPLATE.format(
                        specific_context=specific_context,
                        tag_descriptions=tag_descriptions_structured.into_str(sep="\n"),
                    )
                )
            )
            .into_str()
        )

    def to_tag_and_score_pairs(self) -> list[tuple[str, float]]:
        return self.model_dump().items()

    @classmethod
    def from_llm(
        cls,
        llm: ChatOpenAI,
        docs: dict[LiteNode, dict[str, Any]],
    ) -> Self:
        user_prompt = build_scoring_user_prompt_from_docs(docs=docs)
        content_raw = llm.generate_response(
            system_prompt=cls.system_prompt(),
            user_prompt=user_prompt,
            output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
        )
        return cls.parse_raw(content_raw)


class CodebaseAudienceScores(Scorable):
    internal_user: float
    internal_dev: float
    end_user: float
    end_dev: float
    system: float
    researcher: float

    @classmethod
    def tag_descriptions(cls) -> dict[str, str]:
        assert set(cls.model_fields.keys()) == set(AUDIENCE_MAP.keys())
        return AUDIENCE_MAP

    @classmethod
    def system_prompt(cls) -> str:
        specific_context = """
You are scoring tags for the intended or relevant audiences for the codebase. That is, higher scores should go to audience tags that most directly benefits from or interact with the codebase. In the case that multiple tags are relevant, it is important to score them all with high values but also differentiate based on the most to least relevant in context. For example, an important embedded firmware library may be highly relevant for both "internal_dev" and "system". As a core program for product delivery, "internal_dev" should receive a higher score than the "system" tag, but both should be high.
"""
        tag_descriptions_map = cls.tag_descriptions()
        tag_descriptions_structured = Prompt.empty()
        for k, v in tag_descriptions_map.items():
            tag_descriptions_structured.append(f"{k}: {v}")

        return (
            Prompt.empty()
            .append(
                Component(
                    string=CODEBASE_SCORING_PROMPT_TEMPLATE.format(
                        specific_context=specific_context,
                        tag_descriptions=tag_descriptions_structured.into_str(sep="\n"),
                    )
                )
            )
            .into_str()
        )

    def to_tag_and_score_pairs(self) -> list[tuple[str, float]]:
        return self.model_dump().items()

    @classmethod
    def from_llm(
        cls,
        llm: ChatOpenAI,
        docs: dict[LiteNode, dict[str, Any]],
    ) -> Self:
        user_prompt = build_scoring_user_prompt_from_docs(docs=docs)
        content_raw = llm.generate_response(
            system_prompt=cls.system_prompt(),
            user_prompt=user_prompt,
            output_cfg=OutputConfig(kind=OutputConfigKind.JSON_STRICT, payload=cls),
        )
        return cls.parse_raw(content_raw)
