from datetime import datetime

import boto3
from database.models_v1 import Codebase, UsageEvent, UsageEventType, UsageSession
from sqlmodel import Session, select

from shared.interfaces.usage.event_metadata import (
    UsageMetric,
    UsagePaymentSessionMetadata,
)
from shared.interfaces.usage.usage_schema import (
    UsageBalance,
    UsageCharge,
    UsageEventRange,
    UsageEventSummary,
    UsageMetricUnitType,
)
from shared.repositories.base_repository import BaseRepository
from shared.repositories.usage_event_repository import UsageEventRepository
from shared.usage.llm_session import LLMUsageSession


class UsageService:
    def __init__(self, session: Session, aws_client: boto3.client = None) -> None:
        self.session = session
        self.usage_event_repository = UsageEventRepository(session)
        self.usage_session_repository = BaseRepository(session, UsageSession)
        self.codebase_repository = BaseRepository(session, Codebase)
        self.aws_client = aws_client

    def issue_usage_credits(
        self,
        organization_id: str,
        user_id: str,
        event_type: UsageEventType,
        credit_amount: int,
    ) -> None:
        session_meta = UsagePaymentSessionMetadata(
            provider="stripe",
            message="payment_succeeded",
            event_kind="stripe_webhook_event",
        )

        # need to get the real org id from the workspace since the org_id passed in is the hashed org_id
        with LLMUsageSession(
            organization_id, user_id, session_meta, aws_client=self.aws_client
        ) as llm_session:
            print(f"Session started: {llm_session.session_id}")
            usage_metric = UsageMetric(
                session_id=llm_session.session_id,
                organization_id=organization_id,
                user_id=user_id,
                event_source="api/v1/usage/webhook",
                bytes_in=credit_amount,
                bytes_out=0,
                tokens_in=0,
                tokens_out=0,
                timestamp=datetime.now(),
                event_type=event_type,
                event_metadata=None,
            )

            llm_session.send_event(usage_metric)
            print(f"Session ended: {llm_session.session_id}")

    def get_usage_balance(self, organization_id: str) -> UsageBalance:
        credits_query = select(UsageEvent).where(
            UsageEvent.organization_id == organization_id,
            UsageEvent.event_type.in_(UsageEventRepository.credit_usage_event_types()),
        )
        usage_event_credit = self.session.exec(credits_query).all()

        debits_query = select(UsageEvent).where(
            UsageEvent.organization_id == organization_id,
            UsageEvent.event_type.in_(
                UsageEventRepository.billable_usage_event_types()
            ),
        )
        usage_event_debit = self.session.exec(debits_query).all()
        credit_balance = sum([event.bytes_in for event in usage_event_credit])
        debit_balance = sum(
            [event.bytes_in + event.bytes_out for event in usage_event_debit]
        )
        usage_balance = UsageBalance(
            credits=credit_balance, debits=debit_balance, unit=UsageMetricUnitType.BYTES
        )
        return usage_balance.convert_to(UsageMetricUnitType.SLOC)

    def get_usage_summary(
        self,
        organization_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> UsageEventSummary:
        onboarding_events = self.usage_event_repository.get_usage_events_by_types(
            organization_id,
            [UsageEventType.ONBOARDING_USAGE_DEBIT],
            start_date,
            end_date,
        )
        onboarding_usage = sum(
            [event.bytes_in + event.bytes_out for event in onboarding_events]
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
        tech_doc_usage = sum(
            [
                event.bytes_in + event.bytes_out
                for event in inspector_events
                if event.event_type == UsageEventType.INSPECTOR_TECH_DOC_USAGE_DEBIT
            ]
        )
        code_diff_usage = sum(
            [
                event.bytes_in + event.bytes_out
                for event in inspector_events
                if event.event_type == UsageEventType.INSPECTOR_CODE_DIFF_USAGE_DEBIT
            ]
        )

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

        platform_credit_events = self.usage_event_repository.get_usage_events_by_types(
            organization_id,
            [
                UsageEventType.BASE_PLATFORM_USAGE_CREDIT,
                UsageEventType.ADDITIONAL_PLATFORM_USAGE_CREDIT,
            ],
            start_date,
            end_date,
        )

        platform_usage_credits = sum(
            [event.bytes_in for event in platform_credit_events]
        )
        # get user seat usage
        user_seat_usage_events = self.usage_event_repository.get_usage_events_by_types(
            organization_id,
            [UsageEventType.USER_SEAT_USAGE_DEBIT],
            start_date,
            end_date,
        )
        user_seat_count = len(user_seat_usage_events)

        usage_event_summary = UsageEventSummary(
            onboarding_usage=onboarding_usage,
            tech_doc_usage=tech_doc_usage,
            code_diff_usage=code_diff_usage,
            agent_pipeline_usage=agent_pipeline_usage,
            pdf_summarization_usage=pdf_summarization_usage,
            platform_usage_credits=platform_usage_credits,
            unit=UsageMetricUnitType.BYTES,
            user_seat_count=user_seat_count,
        )
        return usage_event_summary.convert_to(UsageMetricUnitType.SLOC)

    def get_charges(
        self,
        organization_id: str,
        time_range: UsageEventRange,
    ) -> list[UsageCharge]:
        charges = []
        start_date = time_range.start_date
        end_date = time_range.end_date
        onboarding_usage_events = self.usage_event_repository.get_usage_events_by_types(
            organization_id,
            [
                UsageEventType.ONBOARDING_USAGE_DEBIT,
            ],
            start_date,
            end_date,
        )

        # get distinct session ids
        onboarding_session_ids = {event.session_id for event in onboarding_usage_events}

        onboarding_sessions = self.usage_session_repository.get_all(
            conditions=[UsageSession.id.in_(onboarding_session_ids)]
        )

        for sesh in onboarding_sessions:
            meta = sesh.session_metadata
            codebase_id = meta.get("content_id")
            onboarding_usage_event = next(
                event
                for event in onboarding_usage_events
                if event.session_id == sesh.id
            )
            codebase = self.codebase_repository.get(codebase_id)
            if not codebase:
                print(f"Codebase not found for id: {codebase_id}")
                asset_name = "Deleted Codebase"
            else:
                asset_name = codebase.codebase_name
            charges.append(
                UsageCharge(
                    asset_name=asset_name,
                    event_type=UsageEventType.ONBOARDING_USAGE_DEBIT,
                    timestamp=sesh.created_at,
                    bytes=onboarding_usage_event.bytes_in,
                )
            )

        return charges
