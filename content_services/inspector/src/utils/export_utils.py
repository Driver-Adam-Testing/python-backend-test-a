import re
from os.path import relpath
from pathlib import Path


def extract_markdown_links(text: str) -> list:
    """
    Extracts the URL portion from markdown-style hyperlinks like
    [`text`](url) and ignores any other parentheses in the input.

    Args:
        text (str): The input text.

    Returns:
        List[str]: A list of extracted URLs.
    """
    pattern = r"\[`[^`]+`\]\(([^)]+)\)"
    return re.findall(pattern, text)


# TODO: anchor tags?
def replace_driver_compatible_links_with_markdown_links(
    text: str, source_path: str
) -> str:
    """
    Replaces the URL part of markdown-style hyperlinks like
    [`main`](some-link) with a specified new URL, preserving the link text.

    Args:
        text (str): The input string containing markdown links.
        new_url (str): The new URL to use in place of the original.

    Returns:
        str: The modified text with updated hyperlinks.
    """
    extract_link_pattern = r"\[[^\]]+\]\(([^)]+)\)"
    extracted_link = re.findall(extract_link_pattern, text)
    if not extracted_link:
        return text

    for link in extracted_link:
        link_part = link.split("#")[0]
        anchor_tag = link.split("#")[1] if "#" in link else None
        file_path = Path(
            *Path(link_part).parts[1:]
        )  # Strips the first part of the path
        converted_file_path = file_path.with_suffix(file_path.suffix + ".driver.md")
        new_url = relpath(converted_file_path, source_path)
        new_url = new_url.removeprefix("../")
        if new_url == ".":
            new_url = ""
        if anchor_tag:
            anchor_name = anchor_tag.split(":")[1]
            new_url += "#" + anchor_name
        text = text.replace(link, new_url)

    return text
