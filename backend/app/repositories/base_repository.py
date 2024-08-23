from dataclasses import field
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.orm import joinedload

from sqlmodel import Session, SQLModel, select, asc, desc, func
from typing import Type, TypeVar, Generic, Optional, List, Any

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model

    def get(self, pk_id: UUID) -> Optional[T]:
        return self.session.get(self.model, pk_id)
    
    def get_by_pk(self, **kwargs) -> Optional[T]:
        """
        Retrieve an instance by its primary key(s).
        
        :param kwargs: Key-value pairs of primary key fields and their values.
        :return: The instance if found, otherwise None.
        """
        query = select(self.model)
        for key, value in kwargs.items():
            query = query.where(getattr(self.model, key) == value)
        return self.session.exec(query).first()

    def get_by_conditions(self, conditions: List, joins: Optional[List[Type[SQLModel]]] = None):
        query = select(self.model)
        if joins:
            for join_model in joins:
                query = query.join(join_model)
        for condition in conditions:
            query = query.where(condition)
        return self.session.exec(query).first()
    
    def get_all(
            self,
            limit: int = 100,
            offset: int = 0,
            sort_by: Optional[str] = None,
            sort_direction: str = "DESC",
            conditions: Optional[List] = None,
            joins: Optional[List[Type[SQLModel]]] = None
    ) -> List[T]:
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
                raise ValueError(f"Invalid sort field '{sort_by}' for model '{self.model.__name__}'.")

            field_name = f"{self.model.__tablename__}.{sort_by}"
            if sort_direction.upper() == "ASC":
                statement = statement.order_by(asc(text(field_name)))
            elif sort_direction.upper() == "DESC":
                statement = statement.order_by(desc(text(field_name)))
            else:
                raise ValueError("Invalid sort direction provided. Options are ASC or DESC")

        return self.session.exec(statement).all()

    def create(self, obj_in: T) -> T:
        self.session.add(obj_in)
        self.session.commit()
        self.session.refresh(obj_in)
        return obj_in

    def update(self, instance: T, data: T) -> T:
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(instance, key, value)
        self.session.add(instance)
        self.session.commit()
        self.session.refresh(instance)
        return instance

    def delete(self, pk_id: UUID) -> Optional[T]:
        obj = self.get(pk_id)
        if obj:
            self.session.delete(obj)
            self.session.commit()
        return obj
   
    def delete_by_pk(self, **kwargs) -> Optional[T]:
        obj = self.get_by_pk(**kwargs)
        if obj:
            self.session.delete(obj)
            self.session.commit()
        return obj

    def exists(self, id: UUID, organization_id: str | None = None) -> bool:
        instance = self.get(id)
        if not instance:
            return False
        if organization_id is not None:
            return getattr(instance, 'organization_id', None) == organization_id
        return True
    
    def count_by(self, conditions: List, joins: Optional[List[Type[SQLModel]]] = None) -> int:
        query = select(func.count()).select_from(self.model)
        if joins:
            for join_model in joins:
                query = query.join(join_model)
        for condition in conditions:
            query = query.where(condition)
        return self.session.exec(query).one()

    def is_authorized(self, id: UUID, relationship_chain: Optional[List[str]] = None, field_name: Optional[str] = None,
               field_value: Optional[Any] = None) -> bool:
        query = select(self.model).where(self.model.id == id)

        if relationship_chain and field_name and field_value:
            # Traverse the relationship chain
            current_model = self.model
            for relationship in relationship_chain:
                query = query.options(joinedload(getattr(current_model, relationship)))
                current_model = getattr(current_model, relationship).property.mapper.class_

            # Add the condition on the final model in the chain
            query = query.where(getattr(current_model, field_name) == field_value)

        instance = self.session.exec(query).first()
        return instance is not None