from shared.prompts.structured_prompting import (
    Component,
    Prompt,
)

_GENERAL_DEEP_CONTEXT_PREFACE = Prompt.empty().append(
    Component(
        string="""
Your task is to build deep context documents for codebases for downstream LLM agent consumption. That is, you will pre-compile information on specific topics ahead of time for codebases so that downstream LLM agent chat/interactions can be greatly improved. A common issue for large codebases an LLM was not trained on, is that LLM agents equipped with only basic file discovery tools or even indexing that supports semantic search cannot effectively or timely navigate to the sets of places in the codebase critical for input tasks. To resolve this, we can pre-compute information about these codebases ahead of time and provide this in the form documents. You will write an exhaustive and information dense document in this manner. Through integrations such as an MCP service, this information can be fetched and referred to trivially quickly when a downstream LLM agent needs to help a user in real time.
"""
    )
)


_GENERAL_DEEP_CONTEXT_POSTFACE = Prompt.empty().append(
    Component(
        string="""
In your document, do not allude to the fact that this is being written for an LLM. Just write the content of the document per the instructions.
  """
    )
)


_ARCHITECTURE_DOC_GOAL = Prompt.empty().append(
    Component(
        string="""
Your focus in particular is to build an Architecture Overview deep context document. The goal is to provide a document that explains the architecture of the codebase effectively but densely, so that given a broad task (e.g., consider a 10 million line codebase), an LLM agent can refer to this document first and then be very efficient in subsequent steps because this architecture document provided all of the context needed. An architecture document can take many forms depending on the context, but you should focus on the best dense representation for an LLM to quickly reason appropriately about the architecture of a codebase, such as its major components, how they fit together, and where they are implemented.

Write an architecture document for this codebase for the purpose articulated above.
"""
    )
)


_LLM_ONBOARDING_GUIDE_GOAL = Prompt.empty.append(
    Component(
        string="""
Your focus in particular is to build an Onboarding Guide deep context document. The idea is to provide a document that best "onboards" an LLM agent to the codebase, enabling the LLM coding agent to immediately know what to do/where to go next in its workflows to accomplish user's tasks (e.g., as input in an IDE chat experience). You should focus on dense text, and potentially formats such as a table, optimal for use by an LLM agent. Density and exhaustiveness are critical but fundamentally a tradeoff.

Consider an LLM coding agent given a broad task in the context of a very large codebase (e.g., consider a 10 million line codebase). We want to build a deep context LLM onboarding guide that the LLM agent can refer to first and then be very efficient in subsequent steps because this document provided all of the context needed.

Focus on ways of best describing the contents of the codebase itself (capabilities, critical components, interactions, important components to consider together or cross-reference, etc.) rather than any instruction on anything like what an LLM agent should do in its workflow. The goal is to provide all of the information necessary about the codebase so that an LLM agent is equipped to make these decisions on its own.

Write an LLM onboarding guide for this codebase for the purpose articulated above.
        """
    )
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
