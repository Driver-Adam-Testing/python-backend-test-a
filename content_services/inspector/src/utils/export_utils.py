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
    ".cs": ".",
    ".ts": ".",
    ".js": ".",
    ".tsx": ".",
    ".jsx": ".",
    ".rb": "::",
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
    node_path_to_kind: dict,
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
    # extract_link_pattern = r"\[[^\]]+\]\(<([^)]+)>\)"
    extract_link_pattern = r"\[[^\]]+\]\(\<?([^>)]+)\>?\)"
    extracted_links = list(re.finditer(extract_link_pattern, text))
    if not extracted_links:
        return text

    for match in extracted_links:
        full_match = match.group(0)
        link = match.group(1)
        try:
            link_part = link.split("#")[0]
            node_kind_of_link = node_path_to_kind[Path(link_part)]
            anchor_tag = link.split("#")[1] if "#" in link else None
            file_path = Path(
                *Path(link_part).parts[1:]
            )  # Strips the first part of the path
            if anchor_tag is not None and (
                anchor_tag[0] == "L" or anchor_tag[1] == "L"
            ):
                num_parts = len(file_path.parts)
                # NOTE: in order to take advantage of the relative pathing in GFM, we must navigate up from
                # driver_docs/{codebase_name}/{path_part_1}/{path_part_2}/.../{file_path}.md
                # to the source file path at {path_part_1}/{path_part_2}/.../{file_path}
                navigation_parts = "../../" + "../" * (num_parts - 1)
                # strip anything after the '-' in the anchor tag
                anchor_tag = anchor_tag.split("-")[0]  # e.g. L1234
                new_url = f"{navigation_parts}{file_path}#{anchor_tag}"
                replaced_match = full_match.replace(link, new_url)
                text = text.replace(full_match, replaced_match)
                continue  # Skip further processing for line links
            if node_kind_of_link.value == "CODEBASE_FILE":
                converted_file_path = file_path.with_suffix(file_path.suffix + ".md")
            else:
                if file_path.name == ".github":
                    # NOTE: we special case .github here, because Github priotizes displaying
                    # the README.md file from the .github folder over the README.md file in the root of the repo
                    converted_file_path = file_path / "README_.md"
                else:
                    converted_file_path = file_path / "README.md"
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
                if tag_type == "callable":
                    link_name = "".join(  # NOTE: we do an empty join here because the GFM anchor tags strip out special characters (including : and .)
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
                new_url += "#" + link_name.lower()
            replaced_match = full_match.replace(link, new_url)
            text = text.replace(full_match, replaced_match)
        except ValueError as e:
            # This specifically errors in the case of this file, since the tech doc contains an invalid link
            # But could occur elsewhere where these patterns naturally occur in our tech docs. We should
            # just ignore and continue.
            print(f"Error converting file path: {e}")
            continue
        except KeyError as e:
            # This error occurs if there are links in the tech docs that don't adhere to the expected format.
            # Perhaps the link was produced as part of the tech doc itself, as is occurring with python-backend
            print(f"Error converting file path: {e}")
            continue

    return text
