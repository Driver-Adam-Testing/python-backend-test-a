from pydantic import BaseModel


class DataScope(BaseModel):
    """
    Scope of the agent's operation.

    Attributes:
        paths (list[str]): List of paths the agent can access.
        organization_id (str | None): The organization ID.
    """

    paths: list[str] = []
    organization_id: str | None = [None]

    def authorize(self, paths: list[str] | None) -> bool:
        """
        Verify that a list of paths is within the allowed data scope.

        Args:
            paths (list[str]): The list of paths to verify.
        """
        if self.organization_id is None:
            raise ValueError("The organization_id field must be set.")
        if paths is None:
            return True
        for path in paths:
            if not any(
                path == allowed_path or path.startswith(f"{allowed_path}")
                for allowed_path in self.paths
            ):
                raise ValueError(f"Path '{path}' is not within the allowed data scope.")
        return True
