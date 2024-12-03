from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import text
from sqlmodel import Session, SQLModel, asc, desc, func, select

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    def __init__(self: "BaseRepository", session: Session, model: type[T]) -> None:
        self.session = session
        self.model = model

    def get(self: "BaseRepository", pk_id: UUID) -> T | None:
        return self.session.get(self.model, pk_id)

    def get_by_pk(self: "BaseRepository", **kwargs: dict[str, Any]) -> T | None:
        """
        Retrieve an instance by its primary key(s).

        :param kwargs: Key-value pairs of primary key fields and their values.
        :return: The instance if found, otherwise None.
        """
        query = select(self.model)
        for key, value in kwargs.items():
            query = query.where(getattr(self.model, key) == value)
        return self.session.exec(query).first()

    def get_by_conditions(
        self: "BaseRepository",
        conditions: list,
        joins: list[type[SQLModel]] | None = None,
    ) -> T | None:
        query = select(self.model)
        if joins:
            for join_model in joins:
                query = query.join(join_model)
        for condition in conditions:
            query = query.where(condition)
        return self.session.exec(query).first()

    def get_all(
        self: "BaseRepository",
        limit: int = 100,
        offset: int = 0,
        sort_by: str | None = None,
        sort_direction: str = "DESC",
        conditions: list | None = None,
        joins: list[type[SQLModel]] | None = None,
    ) -> list[T]:
        statement = select(self.model).offset(offset).limit(limit)

        if joins:
            for join_model in joins:
                statement = statement.join(join_model)

        if conditions:
            for condition in conditions:
                statement = statement.where(condition)

        if sort_by:
            # Check if the sort field exists on the model
            if not hasattr(self.model, sort_by):
                raise ValueError(
                    f"Invalid sort field '{sort_by}' for model '{self.model.__name__}'."
                )

            field_name = f"{self.model.__tablename__}.{sort_by}"
            if sort_direction.upper() == "ASC":
                statement = statement.order_by(asc(text(field_name)))
            elif sort_direction.upper() == "DESC":
                statement = statement.order_by(desc(text(field_name)))
            else:
                raise ValueError(
                    "Invalid sort direction provided. Options are ASC or DESC"
                )

        return self.session.exec(statement).all()

    def create(self: "BaseRepository", obj_in: T) -> T:
        self.session.add(obj_in)
        self.session.commit()
        self.session.refresh(obj_in)
        return obj_in

    def update(self: "BaseRepository", instance: T, data: T) -> T:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(instance, key, value)
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def delete(self: "BaseRepository", pk_id: UUID) -> T | None:
        obj = self.get(pk_id)
        if obj:
            self.session.delete(obj)
            self.session.commit()
        return obj

    def delete_by_pk(self: "BaseRepository", **kwargs: dict[str, Any]) -> T | None:
        obj = self.get_by_pk(**kwargs)
        if obj:
            self.session.delete(obj)
            self.session.commit()
        return obj

    def exists(
        self: "BaseRepository", id: UUID, organization_id: str | None = None
    ) -> bool:
        instance = self.get(id)
        if not instance:
            return False
        if organization_id is not None:
            return getattr(instance, "organization_id", None) == organization_id
        return True

    def count_by(
        self: "BaseRepository",
        conditions: list,
        joins: list[type[SQLModel]] | None = None,
    ) -> int:
        query = select(func.count()).select_from(self.model)
        if joins:
            for join_model in joins:
                query = query.join(join_model)
        for condition in conditions:
            query = query.where(condition)
        return self.session.exec(query).one()
