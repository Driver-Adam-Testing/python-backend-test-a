from enum import Enum

from shared.interfaces.file_content.file_content import ProcessedFileContent
from shared.interfaces.request import DriverRequest
from shared.interfaces.response import DriverResponse


class Parser(Enum):
    PDF = "pdf"


class ProcessFileRequest(DriverRequest):
    content: str
    file_name: str
    parser: Parser | None = None


class ProcessFileResponse(DriverResponse):
    contents: list[ProcessedFileContent]


def process_file(request: ProcessFileRequest) -> ProcessFileResponse:
    if request.parser == Parser.PDF:
        from shared.pipelines.process_file.file_type_pdf import run_process_pdf

        return ProcessFileResponse(
            contents=run_process_pdf(request.content, request.file_name)
        )
