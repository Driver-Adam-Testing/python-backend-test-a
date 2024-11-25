from datetime import datetime

from database.models_v1 import (
    UsageEvent,
    UsageEventType,
)
from sqlmodel import Session, select

from shared.interfaces.usage.event_metadata import UsageCreditSessionMetadata
from shared.interfaces.usage.usage_schema import (
    UsageBalance,
    UsageEventSummary,
    UsageMetricUnitType,
)
from shared.repositories.usage_event_repository import UsageEventRepository
from shared.usage.usage_session import end_usage_session_sync, start_usage_session_sync


def bytes_to_sloc(bytes: int) -> int:
    return bytes // 50


def sloc_to_bytes(sloc: int) -> int:
    return sloc * 50


class UsageService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.usage_event_repository = UsageEventRepository(session)

    def issue_usage_credits(
        self,
        organization_id: str,
        user_id: str,
        event_type: UsageEventType,
        credit_amount: int,
        event_metadata: dict,
    ) -> None:
        usage_session_id = start_usage_session_sync(
            organization_id,
            user_id,
            UsageCreditSessionMetadata(
                provider="stripe",
                message="payment_succeeded",
                event_kind="stripe_webhook_event",
            ).dict(),
        )
        event = UsageEvent(
            session_id=usage_session_id,
            event_source="stripe_webhook",
            event_type=event_type,
            organization_id=organization_id,
            user_id=user_id,
            bytes_in=credit_amount,
            bytes_out=0,
            tokens_in=0,
            tokens_out=0,
            sloc=bytes_to_sloc(credit_amount),
            timestamp=datetime.now(),
            messages=f"Credit issued to {organization_id} for {credit_amount} bytes",
            event_metadata=event_metadata,
        )
        event = self.usage_event_repository.create(event)
        print(event)
        end_usage_session_sync(usage_session_id)
        print(f"Session ended: {usage_session_id}")

    def get_usage_events(self, organization_id: str) -> list[UsageEvent]:
        """
        get all debit and credit events for an organization
        """
        # get all usage events for an organization

        query = select(UsageEvent).where(
            UsageEvent.organization_id == organization_id,
        )
        usage_events = self.session.exec(query).all()
        return usage_events

    def get_usage_balance(self, organization_id: str) -> UsageBalance:
        """
        get all debit and credit events for an organization
        """
        # get all usage events for an organization

        credits_query = select(UsageEvent).where(
            UsageEvent.organization_id == organization_id,
            UsageEvent.event_type.in_(
                [
                    UsageEventType.BASE_PLATFORM_USAGE_CREDIT,
                    UsageEventType.ADDITIONAL_PLATFORM_USAGE_CREDIT,
                ]
            ),
        )
        usage_event_credit = self.session.exec(credits_query).all()

        debits_query = select(UsageEvent).where(
            UsageEvent.organization_id == organization_id,
            UsageEvent.event_type.in_(
                [
                    UsageEventType.AGENT_PIPELINE_USAGE_DEBIT,
                    UsageEventType.INSPECTOR_TECH_DOC_USAGE_DEBIT,
                    UsageEventType.INSPECTOR_CODE_DIFF_USAGE_DEBIT,
                    UsageEventType.ONBOARDING_USAGE_DEBIT,
                    UsageEventType.SUMMARIZATION_USAGE_DEBIT,
                ]
            ),
        )
        usage_event_debit = self.session.exec(debits_query).all()
        credit_balance = sum([event.bytes_in for event in usage_event_credit])
        debit_balance = sum(
            [event.bytes_in + event.bytes_out for event in usage_event_debit]
        )
        return UsageBalance(
            credits=credit_balance, debits=debit_balance, unit=UsageMetricUnitType.BYTES
        )

    def get_usage_summary(
        self,
        organization_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> UsageEventSummary:
        """
        Get all debit and credit events for an organization within a date range.
        """
        # get onboarding events
        onboarding_events = self.usage_event_repository.get_usage_events_by_types(
            organization_id,
            [UsageEventType.ONBOARDING_USAGE_DEBIT],
            start_date,
            end_date,
        )
        onboarding_usage = sum(
            [event.bytes_in + event.bytes_out for event in onboarding_events]
        )
        onboarding_session_count = len(
            {event.session_id for event in onboarding_events}
        )

        # get inspector events
        inspector_events = self.usage_event_repository.get_usage_events_by_types(
            organization_id,
            [
                UsageEventType.INSPECTOR_TECH_DOC_USAGE_DEBIT,
                UsageEventType.INSPECTOR_CODE_DIFF_USAGE_DEBIT,
            ],
            start_date,
            end_date,
        )
        inspector_usage = sum(
            [event.bytes_in + event.bytes_out for event in inspector_events]
        )
        inspector_session_count = len({event.session_id for event in inspector_events})

        # get agent pipeline events
        agent_pipeline_events = self.usage_event_repository.get_usage_events_by_types(
            organization_id,
            [UsageEventType.AGENT_PIPELINE_USAGE_DEBIT],
            start_date,
            end_date,
        )
        agent_pipeline_usage = sum(
            [event.bytes_in + event.bytes_out for event in agent_pipeline_events]
        )
        agent_pipeline_session_count = len(
            {event.session_id for event in agent_pipeline_events}
        )

        # get pdf summarization events
        pdf_summarization_events = (
            self.usage_event_repository.get_usage_events_by_types(
                organization_id,
                [UsageEventType.SUMMARIZATION_USAGE_DEBIT],
                start_date,
                end_date,
            )
        )
        pdf_summarization_usage = sum(
            [event.bytes_in + event.bytes_out for event in pdf_summarization_events]
        )
        pdf_summarization_session_count = len(
            {event.session_id for event in pdf_summarization_events}
        )

        return UsageEventSummary(
            onboarding_usage=onboarding_usage,
            inspector_usage=inspector_usage,
            agent_pipeline_usage=agent_pipeline_usage,
            pdf_summarization_usage=pdf_summarization_usage,
            onboarding_session_count=onboarding_session_count,
            inspector_session_count=inspector_session_count,
            agent_pipeline_session_count=agent_pipeline_session_count,
            pdf_summarization_session_count=pdf_summarization_session_count,
            unit=UsageMetricUnitType.BYTES,
        )
