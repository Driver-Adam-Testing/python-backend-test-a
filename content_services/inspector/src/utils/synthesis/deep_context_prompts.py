from shared.prompts.structured_prompting import (
    Component,
    Prompt,
)

ARCHITECTURE_OVERVIEW_INTENT = (
    Prompt.empty()
    .append(
        Component(
            string="""
I am trying to build deep context documents for LLM agent consumption. That is, I want to pre-compile information on specific topics ahead of time for codebases so that downstream LLM agent chat/interactions can be greatly improved. A common issue for large codebases an LLM was not trained on, is that LLM agents equipped with only basic file discovery tools or even indexing that supports semantic search cannot effectively or timely navigate to the sets of places in the codebase critical for input tasks. Our approach is to pre-compute exhaustive and information dense documents that can be referred to trivially quickly when a downstream LLM agent needs to help a user in real time. I want to build an Architecture Overview deep context document. The idea is to provide a document that explains the architecture of the codebase effectively but densely for the needs of an LLM agent, so that given a broad task (e.g., consider a 10 million line codebase), an LLM agent can refer to this document first and then be very efficient in subsequent steps because this architecture document provided all of the context needed. An architecture document can take many forms depending on the context, but focus on the best dense representation for an LLM to quickly reason appropriately about the architecture of a codebase, such as its major components, how they fit together, and where they are implemented.

Write an architecture document for this codebase for the purpose articulated above.
"""
        )
    )
    .into_str()
)

LLM_ONBOARDING_INTENT = (
    Prompt.empty()
    .append(
        Component(
            string="""
We are building deep context documents for LLM agent consumption. That is, we want to pre-compile information on specific topics ahead of time about software codebases so that downstream LLM agent chat/interactions can be greatly improved. A common issue for large codebases an LLM was not trained on, is that LLM agents equipped with only basic file discovery tools or even indexing that supports semantic search cannot effectively or timely navigate to the sets of places in the codebase critical for input tasks. Our approach is to pre-compute information ahead of time in the form of *deep context documents* that provides exhaustive and dense information. Through integrations such as an MCP service, this information can be fetched and referred to trivially quickly when a downstream LLM agent needs to help a user in real time.

I want to build an LLM Onboarding Guide deep context document. The idea is to provide a document that best "onboards" an LLM agent to the codebase, enabling the LLM coding agent to immediately know what to do/where to go next in its workflows to accomplish user's tasks (e.g., as input in an IDE chat experience). We should focus on dense text, and potentially formats such as a table, optimal for use by an LLM. Density and exhaustiveness are critical but fundamentally a tradeoff.

Consider an LLM coding agent given a broad task in the context of a very large codebase (e.g., consider a 10 million line codebase). We want to build a deep context LLM onboarding guide that the LLM agent can refer to first and then be very efficient in subsequent steps because this document provided all of the context needed.

Focus on ways of best describing the contents of the codebase itself (capabilities, critical components, architecture, interactions, important components to consider together or cross-reference, etc.) rather than any instruction on anything like what an LLM agent should do in its workflow. The goal is to provide all of the information necessary about the codebase so that an LLM agent is equipped to make these decisions on its own.

Write an LLM onboarding guide for this codebase for the purpose articulated above.
"""
        )
    )
    .into_str()
)
