from enum import Enum
from typing import Annotated

from fastapi import Depends, HTTPException
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

    Examples:
      GET /...?parent_node.relative_path__in=infinity-core/,some-other-path
        => .where(Node.parent_node.has(Node.relative_path.in_(...)))
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
        print(key, value)
        # Separate out operator if present
        split_param = key.split("__", 1)
        field_name = split_param[0]  # e.g. "parent_node.relative_path"
        op = (
            split_param[1]
            if len(split_param) > 1
            else ("in" if isinstance(value, str) and "," in value else "default")
        )

        # Split dot-notation
        parts = field_name.split(".")  # e.g. ["parent_node", "relative_path"]

        # Make sure the operator is valid
        if op not in OPERATORS:
            raise HTTPException(
                status_code=400, detail=f"Unsupported filter operator: {op}"
            )

        # Convert comma-separated values for 'in'/'nin'
        if op in ("in", "nin") and isinstance(value, str):
            value = value.split(",")

        # CASE 1: No relationship
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

        def apply_recursive_filter(
            model: any, parts: list[str], value: any, op: str
        ) -> any:
            if len(parts) == 1:
                col_name = parts[0]
                if not hasattr(model, col_name):
                    raise HTTPException(
                        status_code=400,
                        detail=f"'{col_name}' is not a column on '{model.__name__}'.",
                    )
                column = getattr(model, col_name)
                return OPERATORS[op](column, value)

            rel_name = parts[0]
            if not hasattr(model, rel_name):
                raise HTTPException(
                    status_code=400, detail=f"Invalid relationship: {rel_name}"
                )

            rel_attr = getattr(model, rel_name)
            if not (
                isinstance(rel_attr, InstrumentedAttribute)
                and hasattr(rel_attr, "property")
                and isinstance(rel_attr.property, RelationshipProperty)
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"'{rel_name}' is not a scalar relationship on '{model.__name__}'. "
                        "Cannot apply '.has()' or '.any()' filter."
                    ),
                )

            related_model = rel_attr.property.mapper.class_
            sub_filter_expr = apply_recursive_filter(
                related_model, parts[1:], value, op
            )

            if rel_attr.property.uselist:
                return rel_attr.any(sub_filter_expr)
            else:
                return rel_attr.has(sub_filter_expr)

        print(parts)
        if len(parts) > 1:
            filter_expr = apply_recursive_filter(model, parts, value, op)
            query = query.where(filter_expr)

    return query


def apply_sorting_to_query(
    query: Select, pagination: PaginationQueryParams, model: SQLModel
) -> Select:
    if pagination.sort_by:
        if hasattr(model, pagination.sort_by):
            sort_column = getattr(model, pagination.sort_by)
            query = query.order_by(
                sort_column.asc()
                if pagination.sort_direction == SortDirection.ASC
                else sort_column.desc()
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid sort field")

    query = query.limit(pagination.limit).offset(pagination.offset)
    return query
