import uuid

from sqlmodel import Field, SQLModel, UniqueConstraint

from ..models_enums import TeamRole


class Team(SQLModel, table=True):
    __tablename__ = "team"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_team_org_name"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    organization_id: str = Field(foreign_key="organization.id", index=True)
    name: str


class TeamMembership(SQLModel, table=True):
    __tablename__ = "team_membership"
    __table_args__ = (UniqueConstraint("team_id", "user_id", name="uq_team_member"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    team_id: uuid.UUID = Field(foreign_key="team.id", index=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    role: TeamRole
