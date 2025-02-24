import json
import re


class ParseOutputError(Exception):
    """Exception raised when no valid JSON can be parsed from the input."""

    def __init__(self, message: str, input_str: str) -> None:
        self.input_str = input_str
        super().__init__(f"{message}: {input_str}")


def parse_response_string(str_to_parse: str) -> dict | list:
    """
    Scans the input string for valid JSON objects/arrays.
      - Surrounding or interspersed text is ignored.
      - Every time we see '{' or '[', we attempt to parse a JSON object/array.
      - If it parses successfully, we jump beyond it and continue scanning.
      - If it fails, we skip that bracket and try again on the next one.

    Return rules:
      - If no valid JSON is found, raise ParseOutputError.
      - If exactly one valid JSON object/array is found, return that object.
      - If multiple objects/arrays are found, return them in a list.
    """

    # Optional overall cleanup: replace single quotes with double quotes,
    # remove trailing commas before '}' or ']'.
    candidate = str_to_parse.replace("'", '"')
    candidate = re.sub(r",\s*(?=[}\]])", "", candidate)

    results = []
    decoder = json.JSONDecoder()
    i = 0
    length = len(candidate)

    while i < length:
        # Find the next '{' or '[' from position i
        match = re.search(r"[{\[]", candidate[i:])
        if not match:
            break  # No more JSON starts found

        # Calculate the absolute index of the bracket in the string
        start_index = i + match.start()

        try:
            # Attempt to decode JSON starting at 'start_index'
            obj, end_index = decoder.raw_decode(candidate, start_index)
            results.append(obj)
            # Move 'i' to the position where that JSON object ended
            i = end_index
        except json.JSONDecodeError:
            # If it fails, skip just this bracket and keep searching
            i = start_index + 1

    # Decide how to return results
    if not results:
        raise ParseOutputError("No valid JSON found", str_to_parse)
    if len(results) == 1:
        return results[0]
    return results
