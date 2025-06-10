import re
from os.path import relpath
from pathlib import Path

EXTENSION_TO_DELIMITER = {
    ".cpp": "::",
    ".cc": "::",
    ".cxx": "::",
    ".c": "::",
    ".h": "::",
    ".hpp": "::",
    ".hxx": "::",
    ".py": ".",
    ".java": ".",
}

UNSUPPORTED_CHARACTERS_IN_GFM_ANCHORS = ["~", "=", "!", "(", ")", "&", "|", "+"]


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


def replace_driver_compatible_links_with_markdown_links(
    text: str,
    source_path: str,
    file_extension: str,
) -> str:
    """
    Replaces the URL part of markdown-style hyperlinks like
    [`main`](some-link) with a specified new URL, preserving the link text.

    Args:
        text (str): The input string containing markdown links.
        source_path (str): The source path to which the links should be relative.

    Returns:
        str: The modified text with updated hyperlinks.
    """
    # NOTE: for current doc rendering of class methods we do f"{class_name}{EXTENSION_TO_DELIMITER[file_extension]}{method_name}"
    # BUT the links are constructed as f"({file_path}#{symbol_kind}:{fqn})" where fqn can include things like the
    # namespace, etc.
    # This means that the auto-generated anchor tags in Github flavored markdown do not match the FQN and we must account for this.
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
        try:
            converted_file_path = file_path.with_suffix(file_path.suffix + ".driver.md")
            new_url = relpath(converted_file_path, source_path)
            new_url = new_url.removeprefix("../")
            if new_url == ".":
                new_url = ""
            if anchor_tag:
                # TODO: with special character stripping, we need to add an incrementor to the link_name to dedupe in some cases
                tag_type = anchor_tag.split(":")[0]
                fqn = ":".join(
                    anchor_tag.split(":")[1:]
                )  # This remove the CALLABLE/DATA_STRUCTURE prefix
                delimiter = EXTENSION_TO_DELIMITER.get(file_extension)
                if file_extension == ".py":
                    ## Python includes the full module path in the FQN, so we need to strip it down e.g. 'path/to/file.ClassName.methodName'
                    fqn = ".".join(fqn.split(".")[1:])
                if delimiter is None:
                    raise ValueError(f"Unsupported file extension: {file_extension}")
                # Join with "" because Github Flavored Markdown strips out special characters from the auto-anchortags
                print(tag_type)
                if tag_type == "callable":
                    link_name = "".join(
                        fqn.split(delimiter)[-2:]
                    )  # NOTE: this is strongly coupled to how we're choosing to render the names in the tech docs (e.g. `ClassName::methodName`)
                    # TODO: entities with namespaces in C++ in the links may be broken here
                else:
                    # When documenting data structures, we only display the name of the data structure,
                    # so we can just take the last part of the FQN.
                    link_name = fqn.split(delimiter)[-1]
                for char in UNSUPPORTED_CHARACTERS_IN_GFM_ANCHORS:
                    link_name = link_name.replace(char, "")
                # link_name = link_name.split("%")[0] #TODO: there is some potential weirdness with URL encoded links.
                new_url += "#" + link_name
            text = text.replace(link, new_url)
        except ValueError as e:
            # This specifically errors in the case of this file, since the tech doc contains an invalid link
            # But could occur elsewhere where these patterns naturally occur in our tech docs. We should
            # just ignore and continue.
            print(f"Error converting file path: {e}")
            continue

    return text
