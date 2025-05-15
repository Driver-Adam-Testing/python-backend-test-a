from shared.v3.app.static.enums.format_kinds import FormatKind
from shared.v3.interfaces.llm_message import LlmMessage, MessageKind


class FormatKindMessage(LlmMessage):
    message_kind: MessageKind = MessageKind.DEVELOPER

    @classmethod
    def from_context(cls, format_kind: FormatKind) -> "FormatKindMessage":
        if format_kind == FormatKind.CODE_EXAMPLE:
            return FormatKindMessage(
                content=(
                    "Your entire reply must consist of a single fenced code block. "
                    "Wrap the code with triple back-ticks and specify the language immediately "
                    "after the opening ticks (for example, ```python). Do not include any narrative, "
                    "commentary, or blank lines outside the fence. Choose idiomatic, runnable code "
                    "that directly satisfies the user's request, avoiding ellipses and placeholders "
                    "whenever possible. Keep the code self-contained—import only what you need and "
                    "include minimal setup so the user can paste and run it. If an output demonstration "
                    "is required, embed it as comments inside the same block instead of writing outside text. "
                    "Never mix multiple languages in one block; if several snippets are needed, present them "
                    "sequentially in separate fenced sections. Remember: the code block is the only thing that "
                    "should appear in your response."
                )
            )
        elif format_kind == FormatKind.DIAGRAM:
            return FormatKindMessage(
                content=(
                    "Respond solely with a syntactically valid Mermaid diagram enclosed in triple back-ticks: "
                    "mermaid on the first line and on the last. Do not prepend or append any explanations, "
                    "captions, or blank lines. Choose the most appropriate Mermaid diagram type—flowchart, "
                    "sequence, class, etc.—to express the requested information clearly. Use concise, descriptive "
                    "node labels and keep the diagram free of decorative styling commands. Make sure every arrow "
                    "direction, link, and relationship is logically correct and easy to follow. When depicting "
                    "complex structures, break them into subgraphs instead of overcrowding a single view. The "
                    "diagram itself must fully answer the prompt; no supplementary text or code is allowed outside "
                    "the Mermaid block."
                )
            )
        elif format_kind == FormatKind.TEXT:
            return FormatKindMessage(
                content=(
                    "Provide a pure prose answer with no Markdown structures other than basic paragraphs. "
                    "Write in clear, complete sentences that directly address the user's question without digressions. "
                    "Avoid headings, lists, tables, or code fences; the entire response should read like a well-edited "
                    "short article. Use transitional phrases to guide the reader and ensure logical flow from point to point. "
                    "Cite examples descriptively rather than by inserting literal code blocks or diagrams. If you need emphasis, "
                    "prefer plain wording over formatting tricks such as bold or italics."
                )
            )
        elif format_kind == FormatKind.TABLE:
            return FormatKindMessage(
                content=(
                    "Your final output must be a single Markdown table—nothing before it, nothing after it. "
                    "Begin the table immediately and include a header row, a separator row of dashes, and one or more "
                    "body rows with data. Keep each cell's contents short enough to prevent horizontal scrolling on common "
                    "displays. Do not embed lists, code blocks, or additional Markdown formatting inside cells. Align numeric "
                    "columns to the right by inserting colons in the separator row if alignment matters. If a cell would otherwise "
                    "contain multiline content, split it into additional rows instead. Absolutely no narrative, explanation, or blank "
                    "lines may surround the table."
                )
            )
        elif format_kind == FormatKind.LIST:
            return FormatKindMessage(
                content=(
                    "Answer exclusively with a Markdown list, either bulleted or numbered; do not combine the two styles in one response. "
                    "Begin the very first line with the opening list marker—“- ” for bullets or “1. ” for numbers—and continue without "
                    "introductory text. Nest items only when hierarchical structure adds clarity, not for mere decoration. Each top-level "
                    "list item should be a complete thought, written in full sentences when clarity requires. Avoid embedding code blocks, "
                    "tables, or diagrams inside list items. Keep punctuation consistent: end sentences with periods, but omit periods for "
                    "terse phrases used uniformly. The list itself must satisfy the entire request, so no external commentary or pre-amble is allowed."
                )
            )
        elif format_kind == FormatKind.ANY:
            return FormatKindMessage(
                content=(
                    "The response itself must satisfy the entire request, so no external commentary or pre-amble is allowed."
                )
            )
