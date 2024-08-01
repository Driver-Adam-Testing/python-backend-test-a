import enum

from shared.interfaces.file_content.file_content import ProcessedFileContent


class ProcessedPdfFileContentType(enum.Enum):
    EXTRACTED_TABLE = "extracted_table"
    EXTRACTED_TEXT = "extracted_text"
    EXTRACTED_IMAGE_SUMMARY = "extracted_image"
    VISUAL_SUMMARY = "visual_summary"
    TEXT_SUMMARY = "text_summary"


class ProcessedPdfFileContent(ProcessedFileContent):
    open_ai_file_id: str | None = None
    page: int | None = None
    content_type: ProcessedPdfFileContentType
