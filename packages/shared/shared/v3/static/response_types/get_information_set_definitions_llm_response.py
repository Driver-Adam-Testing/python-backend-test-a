import enum

from shared.v3.interfaces.llm_parseable import LlmParseable


class InformationSetDefinitionList(LlmParseable):
    """
    InformationSetDefinitionList is a class that represents a list of information sets.

    Attributes:
        information_sets (list[InformationSetDefinition]): A list of information sets.

    Inner Class:
        InformationSetDefinition: Represents a single information set with the following attributes:
            - name (str): The name of the information set.
            - description (str): A description of the information set.
            - rationale (str): The rationale behind the inclusion of this information set.
    """

    class InformationSetDefinition(LlmParseable):
        name: str
        description: str
        rationale: str

    information_sets: list[InformationSetDefinition]


class InformationSetRetrievalParameters(LlmParseable):
    """
    InformationSetRetrievalParameters is a class that represents the parameters for retrieving an information set.

    Attributes:
        query_strings (list[str]): The query strings to use to retrieve the information set.
        comparison_affirm (str | None): The comparison affirm to use to retrieve the information set.
        comparison_negate (str | None): The comparison negate to use to retrieve the information set.
        source_bounding (SourceBounding): The bounding of the source to use to retrieve the information set.
        query_type (QueryType): The type of query to use to retrieve the information set.
        element_analysis (ElementAnalysis): The element analysis to use to retrieve the information set.
        exhaustiveness (Exhaustiveness): The exhaustiveness to use to retrieve the information set.
        rationale (str): The rationale for why the parameters were chosen.

    Enum Values:
        SourceBounding: FINITE, UNBOUNDED
        QueryType: EXACT_MATCH_KEYWORD, SEMANTIC
        ElementAnalysis: ALL, SEMANTIC_ANALYSIS
        Exhaustiveness: ENFORCE_EXHAUSTIVENESS, BEST_EFFORT, QUICK_AND_DIRTY
    """

    class SourceBounding(str, enum.Enum):
        FINITE = "FINITE"
        UNBOUNDED = "UNBOUNDED"

    class QueryType(str, enum.Enum):
        EXACT_MATCH_KEYWORD = "EXACT_MATCH_KEYWORD"
        SEMANTIC = "SEMANTIC"

    class Exhaustiveness(str, enum.Enum):
        ENFORCE_EXHAUSTIVENESS = "ENFORCE_EXHAUSTIVENESS"
        BEST_EFFORT = "BEST_EFFORT"
        QUICK_AND_DIRTY = "QUICK_AND_DIRTY"

    class ElementAnalysis(str, enum.Enum):
        ALL = "ALL"
        SEMANTIC_ANALYSIS = "SEMANTIC_ANALYSIS"

    query_strings: list[str]
    comparison_affirm: str | None
    comparison_negate: str | None
    source_bounding: SourceBounding
    query_type: QueryType
    element_analysis: ElementAnalysis
    exhaustiveness: Exhaustiveness
    rationale: str
