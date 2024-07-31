# flake8: noqa: E203

from database.db import engine
from database.models_v1 import (
    Chunk,
    ContentMetadata,
    ContentType,
    RuntimeLogAgentError,
    RuntimeLogAgentInstance,
    RuntimeLogAgentMessage,
)
from sqlmodel import Session, select


class VectorDb:
    def __init__(
        self,
        workspace_id: str,
    ) -> None:
        self.workspace_id = workspace_id
        self.engine = engine

    def get_uploaded_files(self, codebase_id: str = None):
        with Session(self.engine) as session:
            statement = (
                select(ContentMetadata)
                .where(ContentMetadata.workspace_id == self.workspace_id)
                .where(
                    ContentMetadata.content_type == ContentType.AUXILIARY_DOCUMENTATION
                )
            )
            if codebase_id:
                statement = statement.where(ContentMetadata.codebase_id == codebase_id)
            # TODO: totally reassess the pdf strategy to not use assistants
            return session.exec(statement).all()

    def get_file_system(self, codebase_id: str = None):
        with Session(self.engine) as session:
            statement = (
                select(ContentMetadata.relative_path)
                .where(ContentMetadata.workspace_id == self.workspace_id)
                .where(ContentMetadata.content_type == ContentType.SOURCE_CODE)
            )
            if codebase_id:
                statement = statement.where(ContentMetadata.codebase_id == codebase_id)
            statement = statement.distinct()
            # TODO: this won't be the source of truth longterm. We should save codebase metadata and statistics from upstream for use in RAG
            return session.exec(statement).all()

    def log_agent(self, codebase_id: str, model: str):
        agent_instance = RuntimeLogAgentInstance(
            workspace_id=self.workspace_id, codebase_id=codebase_id, model=model
        )
        with Session(self.engine) as session:
            session.add(agent_instance)
            session.commit()
            return agent_instance.id

    def log_agent_message(self, agent_instance_id, message):
        agent_message_instance = RuntimeLogAgentMessage(
            agent_instance_id=agent_instance_id, message=message
        )
        with Session(self.engine) as session:
            session.add(agent_message_instance)
            session.commit()
            return agent_message_instance.id

    def log_agent_error(
        self,
        workspace_id: str,
        codebase_id: str,
        model: str,
        error_message: str,
        error_traceback: str,
    ):
        agent_error_instance = RuntimeLogAgentError(
            workspace_id=workspace_id,
            codebase_id=codebase_id,
            model=model,
            error_message=error_message,
            error_traceback=error_traceback,
        )
        with Session(self.engine) as session:
            session.add(agent_error_instance)
            session.commit()
            return agent_error_instance.id

    def get_agent_instance(self, agent_instance_id: str):
        with Session(self.engine) as session:
            agent_instance = session.get(RuntimeLogAgentInstance, agent_instance_id)
            if not agent_instance:
                return None

            agent_messages = session.exec(
                select(RuntimeLogAgentMessage)
                .where(RuntimeLogAgentMessage.agent_instance_id == agent_instance_id)
                .order_by(RuntimeLogAgentMessage.order)
            ).all()

            agent_errors = session.exec(
                select(RuntimeLogAgentError).where(
                    RuntimeLogAgentError.agent_instance_id == agent_instance_id
                )
            ).all()

            chunk_texts = []
            for message in agent_messages:
                agent_message_chunks = session.exec(
                    select(RuntimeLogAgentMessage).where(
                        RuntimeLogAgentMessage.agent_message_id == message.id
                    )
                ).all()
                for message_chunk in agent_message_chunks:
                    chunk = session.get(Chunk, message_chunk.chunk_id)
                    chunk_texts.append(chunk.text)

            return agent_instance, agent_messages, agent_errors, chunk_texts
