import strawberry
from database.models_v1 import DerivedContent, DerivedContentType
from sqlmodel import Session, func, select

from app.api.routes.legacy.api_types import DerivedContentResults
from app.api.routes.legacy.document_set import DerivedContentTypes
from app.api.routes.legacy.orm_ops import get_source_content_by_id


@strawberry.type
class PageInfo:
    total: int
    page: int
    pageSize: int
    totalPages: int


@strawberry.type
class SymbolSetResponse:
    symbols: list[DerivedContentResults]
    pageInfo: PageInfo


def symbol_set(
    session: Session,
    source_content_id: str,
    user_org_id: str,
    page: int = 1,
    page_size: int = 10,
) -> SymbolSetResponse:
    if page < 1:
        raise ValueError("Page must be at least 1.")
    if page_size < 1 or page_size > 500:
        raise ValueError("PageSize must be between 1 and 500.")

    maybe_source_content = get_source_content_by_id(session, source_content_id)

    if not maybe_source_content:
        raise Exception("Source content not found")

    offset = (page - 1) * page_size
    symbols_statement = (
        select(DerivedContent)
        .join(DerivedContentType)
        .where(
            DerivedContent.source_content_id == source_content_id,
            DerivedContentType.type_name == DerivedContentTypes.SYMBOL.value,
        )
        .offset(offset)
        .limit(page_size)
    )
    symbols = session.exec(symbols_statement).all()

    total_symbols_statement = (
        select(func.count())
        .select_from(DerivedContent)
        .join(DerivedContentType)
        .where(
            DerivedContent.source_content_id == source_content_id,
            DerivedContentType.type_name == DerivedContentTypes.SYMBOL.value,
        )
    )
    total_symbols_count_result = session.exec(total_symbols_statement).first()
    total_symbols_count = (
        total_symbols_count_result if total_symbols_count_result else 0
    )

    pageInfo = PageInfo(  # type: ignore
        total=total_symbols_count,
        page=page,
        pageSize=page_size,
        totalPages=(total_symbols_count // page_size)
        + (1 if total_symbols_count % page_size > 0 else 0),
    )
    return SymbolSetResponse(symbols=symbols, pageInfo=pageInfo)  # type: ignore
