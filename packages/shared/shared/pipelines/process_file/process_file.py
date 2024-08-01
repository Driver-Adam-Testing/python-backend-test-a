from enum import Enum

import requests

from shared.interfaces.request import DriverRequest
from shared.interfaces.response import DriverResponse


class Parser(Enum):
    PDF = "pdf"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    AUTO = "auto"


class ProcessFileRequest(DriverRequest):
    url: str
    parser: Parser | None = None


class ProcessFileResponse(DriverResponse):
    status: str
    message: str


def process_file(request: ProcessFileRequest) -> ProcessFileResponse:
    try:
        response = requests.head(request.url, allow_redirects=True)
        if response.status_code == 200:
            if request.parser == Parser.PDF:
                print("PDF")
            elif request.parser == Parser.PYTHON:
                print("python")
            elif request.parser == Parser.JAVASCRIPT:
                print("javascript")
            parser_value = request.parser.value if request.parser else "None"
            return ProcessFileResponse(
                status="success", message=f"URL is valid and parser is {parser_value}"
            )
        else:
            return ProcessFileResponse(
                status="error", message=f"Failed to access URL: {request.url}"
            )
    except requests.RequestException as e:
        return ProcessFileResponse(status="error", message=f"Error occurred: {str(e)}")
