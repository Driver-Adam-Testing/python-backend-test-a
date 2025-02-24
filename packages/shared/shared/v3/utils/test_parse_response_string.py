from shared.v3.utils.parse_response_string import parse_response_string

TEST_STRINGS = [
    """Certainly, I'll execute a tool to gather more context about initializing the ADXL355 driver. Let's use the HybridSearchTool to search for specific information about the initialization process.

{
    "search_query": "the correct search query",
    "parseable_class_name": "HybridSearchTool"
}""",
    """Certainly, I'll execute a tool to gather more context about initializing the ADXL355 driver. Let's use the HybridSearchTool to search for specific information about the initialization process.

```{
    "search_query": "the correct search query",
    "parseable_class_name": "HybridSearchTool"
}```""",
    """

{
    "search_query": "the correct search query",
    "parseable_class_name": "HybridSearchTool",
    "extra_field": {
        "extra_field_1": "extra_field_1_value",
        "extra_field_2": "extra_field_2_value"
    }
}randomtext
""",
    """
```json
{
    "search_query": "the correct search query",
    "parseable_class_name": "HybridSearchTool",
    "extra_field": {
        "extra_field_1": "extra_field_1_value",
        "extra_field_2": "extra_field_2_value"
    }
}```
""",
    """
```json
{
    "search_query": "the correct search query",
    "parseable_class_name": "HybridSearchTool",
    "extra_field": {
        "extra_field_1": "extra_field_1_value",
        "extra_field_2": "extra_field_2_value"
    }
}```
```json
{
    "search_query": "the correct search query",
    "parseable_class_name": "HybridSearchTool",
    "extra_field": {
        "extra_field_1": "extra_field_1_value",
        "extra_field_2": "extra_field_2_value"
    }
}```
""",
    """
```json
[{
    "search_query": "the correct search query",
    "parseable_class_name": "HybridSearchTool",
    "extra_field": {
        "extra_field_1": "extra_field_1_value",
        "extra_field_2": "extra_field_2_value"
    }
},
{
    "search_query": "the correct search query",
    "parseable_class_name": "HybridSearchTool",
    "extra_field": {
        "extra_field_1": "extra_field_1_value",
        "extra_field_2": "extra_field_2_value"
    }
}]```
""",
]


for test_string in TEST_STRINGS:
    try:
        print(parse_response_string(test_string))
    except Exception as e:
        print(f"Error parsing string: {e}")
