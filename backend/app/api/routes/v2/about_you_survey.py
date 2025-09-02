from fastapi import APIRouter, Body
from pydantic import BaseModel
from sqlmodel import select

from app.api.auth import UserToken
from app.api.session import CurrentSession
from database.models import AboutYouSurvey


router = APIRouter()


class SurveyCreate(BaseModel):
    skipped: bool = False
    plans_for_driver: list[str] | None = None
    team_size: str | None = None
    type_of_work: str | None = None
    type_of_work_other: str | None = None


@router.post("/about-you-survey", status_code=204)
def submit_survey(
    session: CurrentSession,
    user: UserToken,
    payload: SurveyCreate = Body(...),
) -> None:
    existing = session.exec(
        select(AboutYouSurvey)
        .where(AboutYouSurvey.organization_id == user.organization_id)
        .where(AboutYouSurvey.user_id == user.user_id)
    ).first()
    if existing is None:
        record = AboutYouSurvey(
            organization_id=user.organization_id,
            user_id=user.user_id,
            skipped=payload.skipped,
            plans_for_driver=None if payload.skipped else payload.plans_for_driver,
            team_size=None if payload.skipped else payload.team_size,
            type_of_work=None if payload.skipped else payload.type_of_work,
            type_of_work_other=None if payload.skipped else payload.type_of_work_other,
        )
        session.add(record)
    else:
        # Overwrite all fields (upsert semantics)
        existing.skipped = payload.skipped
        if payload.skipped:
            existing.plans_for_driver = None
            existing.team_size = None
            existing.type_of_work = None
            existing.type_of_work_other = None
        else:
            existing.plans_for_driver = payload.plans_for_driver
            existing.team_size = payload.team_size
            existing.type_of_work = payload.type_of_work
            existing.type_of_work_other = payload.type_of_work_other
        session.add(existing)
    session.commit()


class SurveySubmittedResponse(BaseModel):
    submitted: bool


@router.get("/about-you-survey-submitted", response_model=SurveySubmittedResponse)
def survey_submitted(session: CurrentSession, user: UserToken) -> SurveySubmittedResponse:
    exists = (
        session.exec(
            select(AboutYouSurvey)
            .where(AboutYouSurvey.organization_id == user.organization_id)
            .where(AboutYouSurvey.user_id == user.user_id)
        ).first()
        is not None
    )
    return SurveySubmittedResponse(submitted=exists)


