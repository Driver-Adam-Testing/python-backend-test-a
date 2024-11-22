import inspect
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Self, TypeVar
from uuid import UUID

import boto3
import openai
from database.db import engine
from database.models_v1 import (
    UsageEventType,
    UsageSession,
    UsageSessionStatus,
)
from sqlalchemy.orm.attributes import flag_modified
from sqlmodel import Session

from shared.agent.chat_openai import ChatOpenAI, OutputConfig
from shared.interfaces.usage.event_metadata import (
    UsageEventMetadata,
    UsageMetric,
    UsageSessionMetadata,
)

_LLMUsageSession = TypeVar("_LLMUsageSession", bound="LLMUsageSession")

aws_client = None


def get_aws_client() -> boto3.client:
    global aws_client
    if aws_client is None:
        aws_client = boto3.client("events", region_name="us-east-1")
    return aws_client


class UsageEventSendError(Exception):
    """
    Exception raised when an error occurs while sending a usage event
    """

    def __init__(
        self,
        message: str = "Error sending usage event",
        original_exception: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.original_exception = original_exception


@dataclass
class LLMUsageSession:
    organization_id: str
    user_id: str
    session_metadata: UsageSessionMetadata
    session_id: UUID | None = None
    client: ChatOpenAI = None
    events_sent: int = 0

    # session: Session = None
    def __post_init__(self) -> None:
        # self.session = Session(engine)
        if self.session_id is None:
            self.session_id = self._start_session()

    def __enter__(self: _LLMUsageSession) -> Self:
        # Create a new session
        return self

    def __exit__(self, exc_type: any, exc_val: any, exc_tb: any) -> None:
        # Close the session depending on the exception or lack thereof
        if exc_type is None:
            status = UsageSessionStatus.COMPLETED
        else:
            status = UsageSessionStatus.FAILED

        self._end_session(status)

    def _start_session(self) -> UUID:
        # Start a new session
        with Session(engine) as session:
            # with self.session.begin():
            usage_session = UsageSession(
                status=UsageSessionStatus.RUNNING,
                organization_id=self.organization_id,
                user_id=self.user_id,
                session_metadata=self.session_metadata.model_dump(),
            )

            session.add(usage_session)
            session.commit()
            session.refresh(usage_session)
            return usage_session.id

    def _end_session(self, status: UsageSessionStatus) -> None:
        # End the current session
        with Session(engine) as session:
            usage_session = session.get(UsageSession, self.session_id)
            usage_session.status = status
            metadata = usage_session.session_metadata or {}
            metadata["events_sent"] = self.events_sent
            usage_session.session_metadata = metadata
            flag_modified(usage_session, "session_metadata")
            session.add(usage_session)
            session.commit()

    def send_event(self, usage_metric: UsageMetric) -> dict:
        client = get_aws_client()

        entry = {
            "Time": datetime.now(),
            "Source": "metrics.client",
            "DetailType": str(
                UsageEventType(usage_metric.event_type)
            ),  # return a more human-readable version of the enum name
            "Detail": json.dumps(usage_metric.model_dump(), default=str),
            "EventBusName": "metrics-event-bus",
            "TraceHeader": str(usage_metric.session_id),
        }

        try:
            response = client.put_events(
                Entries=[entry],
                # EndpointId=endpoint_id  # Include endpoint ID if provided
            )
            self.events_sent += 1
            return response
        except Exception as e:
            print(f"Error sending event: {e}")
            raise UsageEventSendError(original_exception=e)

    def compute_usage(
        self,
        prompts: list[str],
        response: openai.ChatCompletion,
        event_type: UsageEventType,
    ) -> UsageMetric:
        bytes_in = sum([len(prompt.encode("utf-8")) for prompt in prompts if prompt])

        response_message = response.choices[0].message.content

        bytes_out = len(response_message.encode("utf-8")) if response_message else 0
        tokens_in = response.usage.prompt_tokens
        tokens_out = response.usage.completion_tokens

        # Extracting the function names from the callstack to build event_source
        inner = inspect.stack()[2].function
        middle = inspect.stack()[3].function
        outer = inspect.stack()[4].function

        event_metadata = UsageEventMetadata(
            model=self.client.model,
            provider=self.client.client.__class__.__name__,  # get the class name of the client OpenAI or Claude
            input={
                "prompts": [prompt for prompt in prompts if prompt],
            },
            output=json.dumps(
                response, default=str, indent=2
            ),  # TODO: long term we should store in s3
        )

        usage_metric = UsageMetric(
            session_id=self.session_id,
            organization_id=str(self.organization_id),
            user_id=str(self.user_id),
            event_source="/".join([outer, middle, inner]),
            bytes_in=-bytes_in,
            bytes_out=-bytes_out,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            timestamp=datetime.now(),
            event_type=event_type.value,
            event_metadata=event_metadata,
        )

        return usage_metric

    def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        output_cfg: OutputConfig = OutputConfig.default(),
        model: str = "gpt-4o-2024-08-06",
        temperature: int = 0,
        request_timeout: int = 300,
    ) -> str:
        if not self.client:
            self.client = ChatOpenAI(
                model=model,
                temperature=temperature,
                request_timeout=request_timeout,
            )

        response = self.client.generate_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output_cfg=output_cfg,
        )

        usage_metric = self.compute_usage(
            prompts=[system_prompt, user_prompt],
            response=response,
            event_type=UsageEventType.INSPECTOR_TECH_DOC_USAGE_DEBIT,  # TODO: change this to the correct event type
        )
        self.send_event(usage_metric)
        return response.choices[0].message.content
