# Purpose
This Python code file is designed to implement a search functionality that supports keyword-based, semantic, and hybrid search algorithms. It is structured as a library module that can be imported and used in other parts of a software system. The code leverages SQLAlchemy and SQLModel for database interactions, allowing it to query and filter data from a database based on various criteria such as organization ID, node IDs, and content kinds. The search functionality is built around the BM25 algorithm for keyword relevance scoring and a semantic vector-based approach for understanding the contextual meaning of queries and documents.

The file defines several utility functions and public search functions. The utility functions include text tokenization for BM25 scoring and a function to compute an overall score by combining semantic and BM25 scores. The public search functions—`search_content_without_session`, `search_content`, `semantic_search`, `keyword_search`, and `hybrid_search`—provide interfaces for executing different types of searches. These functions manage database sessions, construct SQL queries, and process search results to return them in a structured format. The hybrid search function combines both semantic and keyword search results, deduplicates them, and computes a final score to rank the results. This code is intended to be a backend component of a larger system, providing a robust and flexible search capability.
# Imports and Dependencies

---
- `logging`
- `re`
- `uuid.UUID`
- `database.db.get_session`
- `database.models_v1.ChunkAndEmbedding`
- `database.models_v1.ContentKind`
- `database.models_v1.DerivedContent`
- `database.models_v2.Node`
- `database.models_v2.PrimaryAsset`
- `database.models_v2.Version`
- `rank_bm25.BM25Okapi`
- `sqlalchemy.Select`
- `sqlalchemy.orm.aliased`
- `sqlalchemy.orm.selectinload`
- `sqlmodel.Session`
- `sqlmodel.and_`
- `sqlmodel.asc`
- `sqlmodel.select`
- `shared.embedding.text_embedder.batch_embed_text`
- `shared.interfaces.search.SearchAlgorithm`
- `shared.interfaces.search.SearchInput`
- `shared.interfaces.search.SearchResult`
- `shared.interfaces.search.SearchResults`


# Global Variables

---
### BM25_WEIGHT 
- **Type**: `float`
- **Description**: `BM25_WEIGHT` is a global constant defined as a float with a value of 1.0. It is used in the calculation of overall scores in search algorithms that combine semantic and BM25 scores.
- **Use**: This variable is used to weight the contribution of BM25 scores in the overall scoring function for search results.


---
### CHARS_PER_TOKEN_APPROXIMATION 
- **Type**: `float`
- **Description**: `CHARS_PER_TOKEN_APPROXIMATION` is a constant float value set to 2.5. It represents an approximate ratio of characters per token, which is used to estimate the number of tokens in a given text based on its character length.
- **Use**: This variable is used to calculate the number of tokens in a text by dividing the character count by this approximation.


---
### MAX_BM25_SCORE 
- **Type**: `float`
- **Description**: `MAX_BM25_SCORE` is a constant float value set to 6.0, representing the maximum possible score for the BM25 algorithm in this context. BM25 is a ranking function used in information retrieval to estimate the relevance of documents to a given search query.
- **Use**: This variable is used to normalize BM25 scores when computing overall search relevance scores.


---
### SEMANTIC_SCORE_IGNORE_THRESHOLD 
- **Type**: `float`
- **Description**: `SEMANTIC_SCORE_IGNORE_THRESHOLD` is a constant float value set to 1.25. It represents a threshold for ignoring semantic scores that are below this value in the context of search algorithms.
- **Use**: This variable is used to filter out semantic scores that are considered too low to be relevant in search results.


---
### SEMANTIC_WEIGHT 
- **Type**: `float`
- **Description**: `SEMANTIC_WEIGHT` is a constant float value set to 1.0. It is used as a weight factor in the calculation of overall scores that combine semantic and BM25 scores.
- **Use**: This variable is used to weight the contribution of semantic scores in the overall scoring function for search results.


# Functions

---
### create_filtered_chunk_statement 
The function `create_filtered_chunk_statement` constructs a SQLAlchemy Select statement to filter `ChunkAndEmbedding` records based on organization, node IDs, content kinds, and optionally an embedded query for semantic scoring.
- **Inputs**:
    - `organization_id`: A string representing the ID of the organization to filter the records by.
    - `node_ids`: An optional list of UUIDs representing node IDs to further filter the records.
    - `content_kinds`: An optional list of `ContentKind` objects to filter the records by specific content types.
    - `embedded_query`: An optional list representing the query vector for calculating semantic scores using L2 distance.
- **Control Flow**:
    - An alias `NodeAlias` is created for the `Node` model to facilitate self-joins.
    - The function checks if `embedded_query` is provided; if so, it includes a semantic score calculation using L2 distance in the select statement.
    - If `embedded_query` is not provided, a default semantic score of 0 is used.
    - The statement is configured to load related content and node versions using `selectinload`.
    - The statement joins several tables: `DerivedContent`, `Node`, `Version`, and `PrimaryAsset`, and filters by `organization_id`.
    - If `content_kinds` is provided, the statement is further filtered by the specified content kinds.
    - If `node_ids` is provided, the statement performs a self-join on `Node` using `NodeAlias` to filter by node IDs and their sub-paths.
- **Output**:
    - The function returns a SQLAlchemy `Select` statement configured with the specified filters and joins.


---
### get_bm25_scores 
The `get_bm25_scores` function calculates BM25 scores for a list of texts based on a given query.
- **Inputs**:
    - `query`: The search query string for which BM25 scores are to be calculated.
    - `texts`: A list of documents (strings) that need to be scored against the query.
- **Control Flow**:
    - Tokenize the input query using the `tokenize_for_bm25` function to prepare it for BM25 scoring.
    - Tokenize each document in the `texts` list using the `tokenize_for_bm25` function.
    - Initialize a BM25Okapi model with the tokenized documents.
    - Calculate and return the BM25 scores for the tokenized query using the BM25Okapi model.
- **Output**:
    - A list of BM25 scores corresponding to each document in the `texts` list, indicating their relevance to the query.


---
### hybrid_search 
The `hybrid_search` function performs a combined semantic and keyword search, deduplicates results, computes BM25 scores, and returns sorted search results.
- **Inputs**:
    - `session`: The active SQLModel session used to execute database queries.
    - `input`: An instance of SearchInput containing user-provided search parameters such as query, organization_id, node_ids, content_kinds, limit, and token_limit.
- **Control Flow**:
    - Embed the search query using `batch_embed_text` to prepare for semantic search.
    - Create a SQL statement for semantic search using `create_filtered_chunk_statement` with the embedded query and execute it to get results up to twice the specified limit.
    - Create a SQL statement for lexical search using `create_filtered_chunk_statement` without the embedded query and execute it to get results up to twice the specified limit.
    - Combine results from semantic and lexical searches into a dictionary keyed by chunk ID, preserving semantic scores where available.
    - If no combined results exist, return an empty SearchResults object.
    - Prepare texts from combined results for BM25 scoring and compute BM25 scores using `get_bm25_scores`.
    - Iterate over combined results, compute an overall score using `overall_score`, and accumulate tokens while respecting the token limit.
    - Sort the search results by score in descending order and limit them to the specified number of results.
    - Label each result with a result number in the metadata and return the final SearchResults object.
- **Output**:
    - A SearchResults object containing a list of SearchResult objects, each with content, score, relative path, version display name, version ID, node ID, and metadata.


---
### keyword_search 
The `keyword_search` function performs a keyword-based search using a TS vector and BM25 scoring to return ranked search results.
- **Inputs**:
    - `session`: The active SQLModel session used to execute database queries.
    - `input`: A `SearchInput` object containing the search parameters such as organization ID, node IDs, content kinds, query, and limit.
- **Control Flow**:
    - Create a SQL statement to filter `ChunkAndEmbedding` records based on the organization ID, node IDs, and content kinds, and match the query using a TS vector.
    - Execute the SQL statement using the provided session to retrieve database results.
    - If no results are found, return an empty `SearchResults` object.
    - Prepare texts from the database results for BM25 scoring by concatenating chunk text and relative path.
    - Compute BM25 scores for the prepared texts against the input query.
    - Convert the database results into `SearchResult` objects, calculating an overall score using the BM25 scores.
    - Sort the search results by score in descending order.
    - Limit the number of search results to the specified input limit.
    - Label each result with a result number in the metadata.
    - Return the `SearchResults` object containing the sorted and labeled search results.
- **Output**:
    - A `SearchResults` object containing a list of `SearchResult` objects, each with content, score, metadata, and other relevant information.


---
### overall_score 
The `overall_score` function computes a combined score from semantic and BM25 scores, normalizing and weighting them to produce a final score between 0 and 1.
- **Inputs**:
    - `semantic_score`: The semantic similarity score, which is distance-based and can be None.
    - `bm25_score`: The BM25 score, which indicates relevance and can be None.
- **Control Flow**:
    - Check if `semantic_score` is not None; if so, normalize it to a range of [0,1] by cubing the distance from 1.0, otherwise set `normalized_semantic` to None.
    - Check if `bm25_score` is not None; if so, normalize it using a naive method to a range of [0,1], otherwise set `normalized_bm25` to None.
    - If `normalized_semantic` is None, return `normalized_bm25` if it is not None, otherwise return 0.0.
    - If `normalized_bm25` is None, return `normalized_semantic`.
    - If both normalized scores are available, compute the weighted average using predefined weights and return the result.
- **Output**:
    - A single float representing the combined score, in the range [0,1].


---
### search_content 
The `search_content` function routes a search request to the appropriate search algorithm based on the specified search algorithm type.
- **Inputs**:
    - `session`: The active SQLModel session used to interact with the database.
    - `input`: An instance of `SearchInput` containing the user-provided search configuration, including the search algorithm type and query details.
- **Control Flow**:
    - Check the `algorithm` attribute of the `input` parameter to determine which search algorithm to use.
    - If the algorithm is `KEYWORD`, call the `keyword_search` function with the provided `session` and `input`.
    - If the algorithm is `SEMANTIC`, call the `semantic_search` function with the provided `session` and `input`.
    - If the algorithm is `HYBRID`, call the `hybrid_search` function with the provided `session` and `input`.
    - If the algorithm is not recognized, raise a `ValueError` indicating an unsupported algorithm.
- **Output**:
    - The function returns a `SearchResults` object containing the results of the search operation.


---
### search_content_without_session 
The function `search_content_without_session` manages a database session and calls the `search_content` function with the provided search input.
- **Inputs**:
    - `input`: The `input` parameter is an instance of `SearchInput` that contains the user-provided search input configuration.
- **Control Flow**:
    - The function begins by creating a session using the `get_session` context manager, which ensures that the session is properly opened and closed.
    - Within the session context, the function calls `search_content`, passing the session and the `input` parameter.
    - The result of the `search_content` function call is returned as the output of `search_content_without_session`.
- **Output**:
    - The function returns a `SearchResults` object, which contains the results of the search operation.


---
### semantic_search 
The `semantic_search` function performs a vector-based semantic search using embedded query vectors to retrieve and rank relevant content chunks from a database.
- **Inputs**:
    - `session`: An active SQLModel session used to execute database queries.
    - `input`: A SearchInput object containing the search query and additional parameters like organization_id, node_ids, content_kinds, and limit.
- **Control Flow**:
    - Initialize a logger for debugging purposes.
    - Embed the query text using the `batch_embed_text` function to obtain a vector representation.
    - Create a SQL statement using `create_filtered_chunk_statement` to filter and order content chunks by semantic score.
    - If a limit is specified in the input, apply it to the SQL statement.
    - Execute the SQL statement using the session to retrieve results from the database.
    - If no results are found, return an empty SearchResults object.
    - Iterate over the results, converting each database result into a SearchResult object with calculated overall scores and metadata.
    - Sort the SearchResult objects by score in descending order and apply the limit if specified.
    - Label each result with a result number in the metadata.
    - Return a SearchResults object containing the sorted and labeled search results.
- **Output**:
    - A SearchResults object containing a list of SearchResult objects, each representing a content chunk with its semantic score and metadata.


---
### tokenize_for_bm25 
The function `tokenize_for_bm25` tokenizes a given text into a list of lowercase word tokens suitable for BM25 scoring.
- **Inputs**:
    - `text`: The input text to be tokenized.
- **Control Flow**:
    - The function uses a regular expression to find all word tokens in the input text, including words with apostrophes, and converts the text to lowercase before tokenization.
- **Output**:
    - A list of lowercase word tokens extracted from the input text.


