from shared.prompts.structured_prompting import (
    Component,
    Prompt,
)

_GENERAL_DEEP_CONTEXT_PREFACE = Component(
    string="""
Your task is to build deep context documents for codebases for downstream LLM agent consumption. That is, you will pre-compile information on specific topics ahead of time for codebases so that downstream LLM agent chat/interactions can be greatly improved. A common issue for large codebases an LLM was not trained on, is that LLM agents equipped with only basic file discovery tools or even indexing that supports semantic search cannot effectively or timely navigate to the sets of places in the codebase critical for input tasks. To resolve this, we can pre-compute information about these codebases ahead of time and provide this in the form documents. You will write an exhaustive and information dense document in this manner. Through integrations such as an MCP service, this information can be fetched and referred to trivially quickly when a downstream LLM agent needs to help a user in real time.

Since you are building dense documents for an entire codebase, it is important to be judicious with what you focus on and how much content you produce for each topic. Look for all opportunities to be brief while making sure importance concepts are covered. Only devote a significant amount of content to topics critically important for the codebase and for a downstream agent to be aware of up front. Focus on text output such as paragraphs, lists, and tables. Do not use diagrams and code blocks unless critically important or useful.
"""
)


_GENERAL_DEEP_CONTEXT_POSTFACE = Component(
    string="""
In your document, do not allude to the fact that this is being written for an LLM. Just write the content of the document per the instructions.
  """
)


_ARCHITECTURE_DOC_GOAL = Component(
    string="""
Your focus in particular is to build an Architecture Overview deep context document. The goal is to provide a document that explains the architecture of the codebase effectively but densely, so that given a broad task (e.g., consider a 10 million line codebase), an LLM agent can refer to this document first and then have a good grasp of the overall architecture. An architecture document can take many forms depending on the context, kind, and size of the codebase, but you should focus on the best dense representation for an LLM to quickly reason appropriately about the architecture of a codebase. Focus more on the conceptual level and be exhaustive -- key components and emergent structure rather than low-level mechanical information such as the directory structure. Major architectural components, functionality provided by the codebase as a whole, and how they fit together are prime topics.

Write an architecture document for this codebase for the purpose articulated above.
"""
)


_LLM_ONBOARDING_GUIDE_GOAL = Component(
    string="""
Your focus in particular is to build an Onboarding Guide deep context document. The idea is to provide a document that best "onboards" an LLM agent to the codebase, enabling the LLM coding agent to immediately know what to do/where to go next in its workflows to accomplish user's tasks (e.g., as input in an IDE chat experience). Density and exhaustiveness are critical but fundamentally a tradeoff.

Consider an LLM coding agent given a broad task in the context of a very large codebase (e.g., consider a 10 million line codebase). We want to build a deep context LLM onboarding guide that the LLM agent can refer to first and then be very efficient in subsequent steps because this document provided all of the context needed

Focus on ways of best describing the contents of the codebase itself and how/where to navigate to for more detailed information. Useful topics include capabilities, critical components and where to find their implementations, important components to consider together or in cross-reference and "tips and tricks" for an agent to navigate the codebase. Keep content focused on the codebase and how to navigate it rather than anything else about what an LLM agent should do in its workflow. The goal is to provide all of the information necessary about the codebase so that an LLM agent is equipped to make these decisions on its own.

Write an LLM onboarding guide for this codebase for the purpose articulated above.
        """
)


UPDATER_IDENTITY_PREAMBLE = Component(
    string="""
You are an expert software engineer and technical writier that specializes in updating existing documents about a software codebase when changes are made to the underlying code.
    """
)


DEEP_CONTEXT_DOCS_PREAMBLE = Component(
    string="""
The kind of document to be updated is a "deep context document." Broadly speaking, these documents are intended to be comprehensive and exhaustive on a particular topic but necessarily high level because they are usually the size of 1 -- 3 pages to cover a large scope such as an entire codebase. Any detail will be specific to the kind of document (e.g., an onboarding guide document may require detailed accounting of file path changes).
    """
)


# TODO: Re-use the actual goal to avoid de-sync/DRY
ARCHITECTURE_DOC_DESCRIPTION = Component(
    string="""
The document we will update is an Architecture Overview. The Architecture Overview documents and explains the architecture of a particular codebase in a dense manner. The use case is for an LLM agent to consult this architecture overview first so that it can much more efficiently performs subsequent steps to solve a task. An architecture document will take on various forms depending on the exact context (underlying codebase kind, size, etc.), but common elements will be identification of key components and emergent structure, functionality provided by the codebase as a whole, and how key componewnts they fit together. Accordingly there is more focus on the conceptual level than, for example, mechanical information about the directory structure. Specifically, you are to decide which of the following categories the diff content belongs to, in relation to this kind of document:
    """
)


# TODO: Re-use the actual goal to avoid de-sync/DRY
LLM_ONBOARDING_DOC_DESCRIPTION = Component(
    string="""
The document we will update is an LLM Onboarding Guide. The LLM Onboarding Guide document focuses on how best to enable an LLM coding agent to immediately know what to do/where to go next in workflows to accomplish users' tasks (e.g., as input in an IDE chat experience). Content will vary according to the exact context (underlying codebase kind, size, etc.), but common elements will include identifying the major capabilities of they codebase but especially on how they interact, how to navigate the codebase to find more detailed content for specific topics, and important components to consider together/cross-reference.
    """
)

ARCHITECTURE_OVERVIEW_INTENT = (
    Prompt.empty()
    .append(_GENERAL_DEEP_CONTEXT_PREFACE)
    .append(_ARCHITECTURE_DOC_GOAL)
    .append(_GENERAL_DEEP_CONTEXT_POSTFACE)
    .into_str()
)


LLM_ONBOARDING_INTENT = (
    Prompt.empty()
    .append(_GENERAL_DEEP_CONTEXT_PREFACE)
    .append(_LLM_ONBOARDING_GUIDE_GOAL)
    .append(_GENERAL_DEEP_CONTEXT_POSTFACE)
    .into_str()
)
