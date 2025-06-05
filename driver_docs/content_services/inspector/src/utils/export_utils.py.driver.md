# Purpose
This Python script provides a narrow functionality focused on processing markdown-style hyperlinks within text. It includes two main functions: `extract_markdown_links`, which extracts URLs from markdown links formatted as [`text`](url), and `replace_driver_compatible_links_with_markdown_links`, which modifies these links to be compatible with a specific file structure by appending `.driver.md` to the file paths and adjusting relative paths. The script is designed to handle markdown text, particularly in technical documentation, and includes error handling for invalid links. Overall, it serves as a utility for managing and converting markdown links in documentation files.
# Imports and Dependencies

---
- `re`
- `os.path`
- `pathlib`


# Functions

---
### extract_markdown_links
The function `extract_markdown_links` extracts URLs from markdown-style hyperlinks in a given text.
- **Inputs**:
    - `text`: A string containing markdown-style hyperlinks from which URLs need to be extracted.
- **Control Flow**:
    - Define a regular expression pattern to match markdown-style hyperlinks with URLs.
    - Use `re.findall` to search the input text for all matches of the pattern.
    - Return the list of URLs extracted from the matches.
- **Output**:
    - A list of strings, each representing a URL extracted from the markdown-style hyperlinks in the input text.


---
### replace_driver_compatible_links_with_markdown_links
The function replaces the URL part of markdown-style hyperlinks in a text with a new URL relative to a given source path, preserving the link text.
- **Inputs**:
    - `text`: The input string containing markdown links.
    - `source_path`: The source path to which the links should be relative.
- **Control Flow**:
    - Define a regex pattern to extract URLs from markdown-style links in the input text.
    - Use `re.findall` to extract all links matching the pattern from the input text.
    - If no links are found, return the original text.
    - Iterate over each extracted link and split it into the main link part and an optional anchor tag.
    - Convert the main link part to a `Path` object, stripping the first part of the path.
    - Attempt to convert the file path to a new path with a '.driver.md' suffix and calculate its relative path to the source path.
    - Remove any leading '../' from the new URL and handle the case where the new URL is '.' by setting it to an empty string.
    - If an anchor tag exists, append it to the new URL after extracting the anchor name.
    - Replace the original link in the text with the new URL.
    - Handle any `ValueError` exceptions by printing an error message and continuing the loop.
- **Output**:
    - The function returns the modified text with updated hyperlinks.


