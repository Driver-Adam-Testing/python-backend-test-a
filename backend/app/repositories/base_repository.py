from uuid import UUID

from sqlmodel import Session, SQLModel, select, asc, desc
from typing import Type, TypeVar, Generic, Optional, List, Any

T = TypeVar("T", bound=SQLModel)


class BaseRepository(Generic[T]):
    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model

    def get(self, pk_id: UUID) -> Optional[T]:
        return self.session.get(self.model, pk_id)

    def get_all(
            self,
            limit: int = 100,
            offset: int = 0,
            sort_by: Optional[str] = None,
            sort_direction: str = "DESC"
    ) -> List[T]:
        statement = select(self.model).offset(offset).limit(limit)

        if sort_by:
            # Check if the sort field exists on the model
            if not hasattr(self.model, sort_by):
                raise ValueError(f"Invalid sort field '{sort_by}' for model '{self.model.__name__}'.")
            if sort_direction.upper() == "ASC":
                statement = statement.order_by(asc(getattr(self.model, sort_by)))
            elif sort_direction.upper() == "DESC":
                statement = statement.order_by(desc(getattr(self.model, sort_by)))
            else:
                raise ValueError("Invalid sort direction provided. Options are ASC or DESC")

        return self.session.exec(statement).all()

    def create(self, obj_in: T) -> T:
        self.session.add(obj_in)
        self.session.commit()
        self.session.refresh(obj_in)
        return obj_in

    def update(self, obj: T, obj_in: dict) -> T:
        obj_data = obj.model_dump()
        for field in obj_data:
            if field in obj_in:
                setattr(obj, field, obj_in[field])
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def delete(self, pk_id: UUID) -> Optional[T]:
        obj = self.get(pk_id)
        if obj:
            self.session.delete(obj)
            self.session.commit()
        return obj
