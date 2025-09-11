from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from database.models import OnboardingChecklist


class OnboardingChecklistService:
    def __init__(self, session: Session, organization_id: str, user_id: str) -> None:
        self.session = session
        self.organization_id = organization_id
        self.user_id = user_id
        self._checklist: Optional[OnboardingChecklist] = None

    def get_or_create(self) -> "OnboardingChecklistService":
        """Ensure the checklist exists for this user/org and return self for chaining."""
        checklist = self.session.exec(
            select(OnboardingChecklist)
            .where(OnboardingChecklist.organization_id == self.organization_id)
            .where(OnboardingChecklist.user_id == self.user_id)
        ).one_or_none()

        if checklist is None:
            checklist = OnboardingChecklist(
                organization_id=self.organization_id,
                user_id=self.user_id,
            )
            self.session.add(checklist)
            self.session.commit()
            self.session.refresh(checklist)

        self._checklist = checklist
        return self

    @property
    def checklist(self) -> OnboardingChecklist:
        if self._checklist is None:
            raise RuntimeError("Checklist not loaded. Call get_or_create() first.")
        return self._checklist

    def mark_invite_teammate_completed(
        self, when: datetime | None = None
    ) -> "OnboardingChecklistService":
        if self._checklist is None:
            raise RuntimeError("Checklist not loaded. Call get_or_create() first.")
        if self._checklist.invite_teammate_completed_at is None:
            self._checklist.invite_teammate_completed_at = (
                when or datetime.now(timezone.utc)
            )
            self.session.add(self._checklist)
            self.session.commit()
        return self

    def mark_generate_autodoc_completed(
        self, when: datetime | None = None
    ) -> "OnboardingChecklistService":
        if self._checklist is None:
            raise RuntimeError("Checklist not loaded. Call get_or_create() first.")
        if self._checklist.generate_autodoc_completed_at is None:
            self._checklist.generate_autodoc_completed_at = (
                when or datetime.now(timezone.utc)
            )
            self.session.add(self._checklist)
            self.session.commit()
        return self

    def mark_connect_codebase_completed(
        self, when: datetime | None = None
    ) -> "OnboardingChecklistService":
        if self._checklist is None:
            raise RuntimeError("Checklist not loaded. Call get_or_create() first.")
        if self._checklist.connect_codebase_completed_at is None:
            self._checklist.connect_codebase_completed_at = (
                when or datetime.now(timezone.utc)
            )
            self.session.add(self._checklist)
            self.session.commit()
        return self

    def mark_generate_codebase_completed(
        self, when: datetime | None = None
    ) -> "OnboardingChecklistService":
        if self._checklist is None:
            raise RuntimeError("Checklist not loaded. Call get_or_create() first.")
        if self._checklist.generate_codebase_completed_at is None:
            self._checklist.generate_codebase_completed_at = (
                when or datetime.now(timezone.utc)
            )
            self.session.add(self._checklist)
            self.session.commit()
        return self

    def mark_setup_mcp_completed(
        self, when: datetime | None = None
    ) -> "OnboardingChecklistService":
        if self._checklist is None:
            raise RuntimeError("Checklist not loaded. Call get_or_create() first.")
        if self._checklist.setup_mcp_completed_at is None:
            self._checklist.setup_mcp_completed_at = (
                when or datetime.now(timezone.utc)
            )
            self.session.add(self._checklist)
            self.session.commit()
        return self

    def mark_enable_export_completed(
        self, when: datetime | None = None
    ) -> "OnboardingChecklistService":
        if self._checklist is None:
            raise RuntimeError("Checklist not loaded. Call get_or_create() first.")
        if self._checklist.enable_export_completed_at is None:
            self._checklist.enable_export_completed_at = (
                when or datetime.now(timezone.utc)
            )
            self.session.add(self._checklist)
            self.session.commit()
        return self


