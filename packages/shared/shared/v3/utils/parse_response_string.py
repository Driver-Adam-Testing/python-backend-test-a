import json
import logging
import re
import xml.etree.ElementTree as ET

from pydantic import BaseModel, ValidationError
from shared.v3.globals.constants import PARSEABLE_CLASS_NAME

# Configure logging (this can be adjusted as needed)
logging.basicConfig(level=logging.ERROR)


class ParseOutputError(Exception):
    """Exception raised when output cannot be parsed as JSON or XML."""

    def __init__(self, message: str, input_str: str) -> None:
        self.input_str = input_str
        super().__init__(f"{message}: {input_str}")


class BestFitModelCastError(Exception):
    def __init__(self, data: dict, model_options: list[type[BaseModel]]):
        self.data = data
        self.model_options = model_options
        super().__init__(
            f"Unable to cast data {data} to any of the provided model options: {model_options}"
        )


def parse_response_string(str_to_parse: str) -> dict | list:
    print(f"Parsing response string: \n\n{str_to_parse}\n\n")
    """
    Attempts to convert a string into a dict or list by applying multiple recovery strategies:
    1. Clean common wrappers (like triple backticks with language hints).
    2. Attempt to parse as JSON using several cleaning strategies.
    3. If JSON parsing fails, try to parse as XML and convert it to a dictionary.

    Returns:
        A dictionary or list depending on the parsed content.

    Raises:
        ParseOutputError: If the input string cannot be parsed as either JSON or XML.
    """

    def xml_to_dict(elem: ET.Element) -> dict:
        """
        Recursively converts an XML element and its children into a dictionary.
        Attributes are prefixed with '@' and text content (if mixed with children) is stored under '#text'.
        """
        d = {}
        # Process element attributes.
        if elem.attrib:
            d.update({f"@{k}": v for k, v in elem.attrib.items()})

        # Process children.
        children = list(elem)
        if children:
            child_dict = {}
            for child in children:
                child_obj = xml_to_dict(child)
                tag = child.tag
                if tag in child_dict:
                    # If already exists, convert to list.
                    if not isinstance(child_dict[tag], list):
                        child_dict[tag] = [child_dict[tag]]
                    child_dict[tag].append(child_obj)
                else:
                    child_dict[tag] = child_obj
            d.update(child_dict)

        # Process text content.
        text = elem.text.strip() if elem.text else ""
        if text:
            if d:
                d["#text"] = text
            else:
                d = text
        return d

    def try_parse_json(candidate: str) -> dict | list:
        try:
            result = json.loads(candidate)
            # Only return if it's a dict or list.
            if isinstance(result, (dict, list)):
                return result
        except json.JSONDecodeError:
            return None

    # Step 1: Clean common wrappers (e.g. code fences with optional language hints)
    cleaned = str_to_parse.strip()
    if cleaned.startswith("```"):
        # Remove starting and ending code fences (supporting language hints like json or xml)
        cleaned = re.sub(r"^```[a-zA-Z]*", "", cleaned)
        cleaned = re.sub(r"```$", "", cleaned).strip()

    # Remove any random text around code fences by trying to extract JSON/XML block
    # First try JSON directly.
    result = try_parse_json(cleaned)
    if result is not None:
        return result

    # Try to extract a JSON substring using regex.
    json_substr_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if json_substr_match:
        candidate = json_substr_match.group(0)
        result = try_parse_json(candidate)
        if result is not None:
            return result

    # Replace single quotes with double quotes and try parsing.
    candidate = cleaned.replace("'", '"')
    result = try_parse_json(candidate)
    if result is not None:
        return result

    # Remove trailing commas before closing braces/brackets and try again.
    candidate = re.sub(r",\s*(?=[}\]])", "", candidate)
    result = try_parse_json(candidate)
    if result is not None:
        return result

    # If JSON parsing fails, try to parse as XML.
    try:
        root = ET.fromstring(cleaned)
        xml_result = xml_to_dict(root)
        # Return xml_result as is (if it's not a dict, wrap it)
        if isinstance(xml_result, dict):
            return xml_result
        else:
            return {"root": xml_result}
    except ET.ParseError:
        pass

    logging.error(f"Failed to parse output: {str_to_parse}")
    raise ParseOutputError("Unable to parse the provided output", str_to_parse)


def cast_to_best_fit_model(
    data: dict, model_options: list[type[BaseModel]]
) -> BaseModel:
    """
    Tries to cast the given data to the best fitting BaseModel type from the provided model list.
    Models are scored based on the fraction of their defined fields that are present in the data,
    with a bonus if the model's name matches the global 'PARSEABLE_CLASS_NAME' field.

    :param data: Dictionary containing the data to be cast.
    :param model_options: List of BaseModel types to try casting the data to.
    :return: An instance of the best fitting BaseModel type.
    :raises BestFitModelCastError: If no model can be instantiated successfully.
    """
    # If a parsed_classname hint is provided, try that model first.
    parsed_class_hint = data.get(PARSEABLE_CLASS_NAME)
    if parsed_class_hint:
        for model in model_options:
            if model.__name__ == parsed_class_hint:
                try:
                    return model(**data)
                except (ValidationError, TypeError):
                    # If instantiation fails, we continue to scoring.
                    break

    successful_models = []
    for model in model_options:
        try:
            instance = model(**data)
            model_fields = set(model.model_fields.keys())
            data_keys = set(data.keys())
            matching_keys = model_fields.intersection(data_keys)
            # Compute the ratio of matching keys.
            ratio = len(matching_keys) / len(model_fields) if model_fields else 0
            # Boost the ratio if parsed_classname matches.
            if parsed_class_hint and model.__name__ == parsed_class_hint:
                ratio += 1.0
            successful_models.append((ratio, len(matching_keys), instance))
        except (ValidationError, TypeError):
            continue

    if successful_models:
        best = max(successful_models, key=lambda x: (x[0], x[1]))
        return best[2]

    raise BestFitModelCastError(data, model_options)
