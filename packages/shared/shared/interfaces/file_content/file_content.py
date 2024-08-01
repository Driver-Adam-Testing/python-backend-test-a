from pydantic import BaseModel


class ProcessedFileContent(BaseModel):
    content: str
