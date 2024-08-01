import io
from enum import Enum

from shared.interfaces.file_content.file_content import ProcessedFileContent
from shared.interfaces.request import DriverRequest
from shared.interfaces.response import DriverResponse


class Parser(Enum):
    PDF = "pdf"


class ProcessFileRequest(DriverRequest):
    file_path: str
    parser: Parser | None = None


class ProcessFileResponse(DriverResponse):
    contents: list[ProcessedFileContent]


def process_file(request: ProcessFileRequest) -> ProcessFileResponse:
    if request.parser == Parser.PDF:
        from packages.shared.shared.pipelines.process_file.process_file_pdf import (
            run_process_pdf,
        )

        with open(request.file_path, "rb") as file:
            file_content = io.BytesIO(file.read())
            file_content.name = request.file_path

        return ProcessFileResponse(contents=run_process_pdf(file_content))
