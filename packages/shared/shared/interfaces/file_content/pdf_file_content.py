import enum

from shared.interfaces.file_content.file_content import ProcessedFileContent


class ProcessedPdfFileContentType(enum.Enum):
    EXTRACTED_TABLE = "pdf-extracted-table"
    EXTRACTED_TEXT = "pdf-extracted-text"
    EXTRACTED_IMAGE_SUMMARY = "pdf-image-summary"
    VISUAL_SUMMARY = "pdf-visual-summary"
    TEXT_SUMMARY = "pdf-text-summary"


class ProcessedPdfFileContent(ProcessedFileContent):
    open_ai_file_id: str | None = None
    page: int | None = None
    content_type: ProcessedPdfFileContentType
