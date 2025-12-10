from enum import Enum
from typing import Annotated

from fastapi import Depends, HTTPException

# Import JSONB type for checking JSONB columns
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql import Select
from sqlmodel import SQLModel


class SortDirection(str, Enum):
    ASC = "ASC"
    DESC = "DESC"


class PaginationQueryParams:
    def __init__(
        self,
        limit: int = 10,
        offset: int = 0,
        sort_by: str | None = None,
        sort_direction: SortDirection = SortDirection.DESC,
    ) -> None:
        self.limit = limit
        self.offset = offset
        self.sort_by = sort_by
        self.sort_direction = sort_direction


def get_pagination_params(
    params: PaginationQueryParams = Depends(),
) -> PaginationQueryParams:
    return params


Pagination = Annotated[PaginationQueryParams, Depends(get_pagination_params)]


def apply_filters_to_query(query: Select, filters: dict, model: SQLModel) -> Select:
    """
    Applies filters to a SQLAlchemy/SQLModel 'select' query, based on
    a dictionary of filter keys and values.
      - Supports double-underscore syntax for operators (e.g. 'name__like=foo').
      - If the filter key is "relationship.column__op", uses `.has(...)`
        for scalar relationships rather than a JOIN.
      - If the filter key is "column__op" (no dot), applies the filter on `model.column`.

    Example:
      GET /...?misc_metadata.sloc__eq=245
        => node.misc_metadata["sloc"] == 245
    """

    OPERATORS = {
        "default": lambda col, val: col == val,
        "eq": lambda col, val: col == val,
        "neq": lambda col, val: col != val,
        "in": lambda col, val: col.in_(val),
        "nin": lambda col, val: ~col.in_(val),
        "lt": lambda col, val: col < val,
        "gt": lambda col, val: col > val,
        "lte": lambda col, val: col <= val,
        "gte": lambda col, val: col >= val,
        "like": lambda col, val: col.like(val),
        "ilike": lambda col, val: col.ilike(val),
    }

    for key, value in filters.items():
        # Separate out operator if present
        split_param = key.split("__", 1)
        field_name = split_param[0]
        op = (
            split_param[1]
            if len(split_param) > 1
            else ("in" if isinstance(value, str) and "," in value else "default")
        )

        # Split dot-notation
        parts = field_name.split(".")

        # Make sure the operator is valid
        if op not in OPERATORS:
            raise HTTPException(
                status_code=400, detail=f"Unsupported filter operator: {op}"
            )

        # Convert comma-separated values for 'in'/'nin'
        if op in ("in", "nin") and isinstance(value, str):
            value = value.split(",")

        # CASE 1: No dot-notation means no relationship/JSON indexing needed
        if len(parts) == 1:
            attr_name = parts[0]
            if not hasattr(model, attr_name):
                continue
            attr = getattr(model, attr_name)
            if (
                isinstance(attr, InstrumentedAttribute)
                and hasattr(attr, "property")
                and isinstance(attr.property, RelationshipProperty)
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"'{attr_name}' is a relationship. Please specify a column, "
                        "e.g. 'relationship.column__op=value'."
                    ),
                )

            filter_expr = OPERATORS[op](attr, value)
            query = query.where(filter_expr)
        else:
            # CASE 2: Dot-notation provided. Could be a relationship or JSONB column.
            def apply_recursive_filter(
                model: any, parts: list[str], value: any, op: str
            ) -> any:
                # When there's a single part, just apply the operator directly.
                if len(parts) == 1:
                    col_name = parts[0]
                    if not hasattr(model, col_name):
                        raise HTTPException(
                            status_code=400,
                            detail=f"'{col_name}' is not a column on '{model.__name__}'.",
                        )
                    column = getattr(model, col_name)
                    return OPERATORS[op](column, value)

                # Look up the column on the model
                col_name = parts[0]
                if not hasattr(model, col_name):
                    raise HTTPException(
                        status_code=400,
                        detail=f"'{col_name}' is not a column on '{model.__name__}'.",
                    )
                column = getattr(model, col_name)

                # Check if the column is a JSONB column.
                if hasattr(column, "type") and isinstance(column.type, JSONB):
                    # For JSONB, iterate over the remaining parts to index into the JSON.
                    json_expr = column
                    for key in parts[1:]:
                        json_expr = json_expr[key]
                    return OPERATORS[op](json_expr, value)

                # Otherwise, treat it as a relationship.
                if not (
                    isinstance(column, InstrumentedAttribute)
                    and hasattr(column, "property")
                    and isinstance(column.property, RelationshipProperty)
                ):
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"'{col_name}' is neither a valid column for JSONB extraction "
                            "nor a scalar relationship on '{model.__name__}'."
                        ),
                    )
                related_model = column.property.mapper.class_
                sub_filter_expr = apply_recursive_filter(
                    related_model, parts[1:], value, op
                )
                if column.property.uselist:
                    return column.any(sub_filter_expr)
                else:
                    return column.has(sub_filter_expr)

            filter_expr = apply_recursive_filter(model, parts, value, op)
            query = query.where(filter_expr)

    return query


def apply_sorting_to_query(
    query: Select, pagination: PaginationQueryParams, model: SQLModel
) -> Select:
    """
    Applies sorting and pagination to a SQLAlchemy/SQLModel 'select' query.
    Supports sorting on JSONB columns using dot notation.

    Example:
      GET /...?sort_by=misc_metadata.sloc&sort_direction=ASC
        => ORDER BY node.misc_metadata["sloc"] ASC
    """
    if pagination.sort_by:
        sort_field = pagination.sort_by
        parts = sort_field.split(".")

        if len(parts) == 1:
            if not hasattr(model, sort_field):
                raise HTTPException(status_code=400, detail="Invalid sort field")
            sort_column = getattr(model, sort_field)
        else:
            current_model = model
            for rel_part in parts[:-1]:
                if not hasattr(current_model, rel_part):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid relationship path: '{rel_part}' on '{current_model.__name__}'.",
                    )
                rel_attr = getattr(current_model, rel_part)
                if not (
                    isinstance(rel_attr, InstrumentedAttribute)
                    and hasattr(rel_attr, "property")
                    and isinstance(rel_attr.property, RelationshipProperty)
                ):
                    raise HTTPException(
                        status_code=400,
                        detail=f"'{rel_part}' is not a valid relationship on '{current_model.__name__}'.",
                    )
                related_model = rel_attr.property.mapper.class_
                query = query.outerjoin(rel_attr)
                current_model = related_model

            col_name = parts[-1]
            if not hasattr(current_model, col_name):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid sort field: '{col_name}' on '{current_model.__name__}'.",
                )
            sort_column = getattr(current_model, col_name)

        if pagination.sort_direction == SortDirection.ASC:
            if model.id:
                query = query.order_by(sort_column.asc(), model.id).distinct(
                    sort_column, model.id
                )
            else:
                query = query.order_by(sort_column.asc())
        else:
            if model.id:
                query = query.order_by(
                    sort_column.desc().nulls_last(), model.id
                ).distinct(sort_column, model.id)
            else:
                query = query.order_by(sort_column.desc().nulls_last())

    # Apply pagination
    query = query.limit(pagination.limit).offset(pagination.offset)
    return query
