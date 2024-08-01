from __future__ import annotations

import logging
from collections.abc import Iterator

from strawberry.extensions.base_extension import SchemaExtension

logger = logging.getLogger(__name__)


class LoggingExtension(SchemaExtension):
    def on_execute(self) -> Iterator[None]:
        if self.execution_context.graphql_document:
            logger.info(
                f"Operation {self.execution_context.operation_type} {self.execution_context.operation_name} : Errors {len(self.execution_context.errors)}"
            )
        yield
