class GitProviderAppRevokeError(Exception):
    def __init__(
        self,
        message: str,
        original_exception: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.original_exception = original_exception


class GitProviderAccessTokenError(Exception): ...
