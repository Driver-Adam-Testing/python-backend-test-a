def parse_content_scope(content_scope: str) -> tuple[str, str, str, str]:
    """
    Parses the content_scope string into its individual components.

    Parameters
    ----------
    content_scope : str
        The content scope string in the format 'organization_id:workspace_id:codebase_id:relative_path'.

    Returns
    -------
    tuple
        A tuple containing the organization_id, workspace_id, codebase_id, and relative_path.
    """
    parts = content_scope.split(":")
    if len(parts) != 4:
        raise ValueError(
            "content_scope must be in the format 'organization_id:workspace_id:codebase_id:relative_path'"
        )
    return tuple(parts)


def build_content_scope(
    organization_id: str, workspace_id: str, codebase_id: str, relative_path: str
) -> str:
    """
    Builds the content_scope string from its individual components.

    Parameters
    ----------
    organization_id : str
        The organization ID.
    workspace_id : str
        The workspace ID.
    codebase_id : str
        The codebase ID.
    relative_path : str
        The relative path.

    Returns
    -------
    str
        The content scope string in the format 'organization_id:workspace_id:codebase_id:relative_path'.
    """
    return f"{organization_id}:{workspace_id}:{codebase_id}:{relative_path}"
