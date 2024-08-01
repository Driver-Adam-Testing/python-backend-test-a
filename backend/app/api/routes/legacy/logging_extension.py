import logging
from collections.abc import Iterator

from strawberry.extensions.base_extension import SchemaExtension

logger = logging.getLogger(__name__)


class LoggingExtension(SchemaExtension):
    def on_execute(self) -> Iterator[None]:
        logger.info(
            f"GraphQL : {self.execution_context.operation_type} {self.execution_context.operation_name}"
        )
        yield
