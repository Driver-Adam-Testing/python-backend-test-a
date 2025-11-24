from datetime import timedelta

from hatchet_client import hatchet
from hatchet_sdk import Context
from onboarding.onboard import (
    connect_repos_for_installation,
    handle_azure_devops_events,
    handle_bitbucket_events,
    handle_github_events,
    handle_gitlab_events,
    run_codebase_connection,
)
from pydantic import BaseModel


class HandleGithubEventsInput(BaseModel):
    installation_id: str | None
    org_id: str
    repos_added: list[dict]
    repos_deleted: list[dict]
    repos_pushed: list[dict]


class HandleGitlabEventsInput(BaseModel):
    installation_id: str | None
    org_id: str
    repos_added: list[dict]
    repos_deleted: list[dict]
    repos_pushed: list[dict]


class HandleBitbucketEventsInput(BaseModel):
    installation_id: str | None
    org_id: str
    repos_added: list[dict]
    repos_deleted: list[dict]
    repos_pushed: list[dict]


class HandleAzureDevopsEventsInput(BaseModel):
    installation_id: str | None
    org_id: str
    repos_added: list[dict]
    repos_deleted: list[dict]
    repos_pushed: list[dict]


class ConnectReposForInstallationInput(BaseModel):
    github_installation_id: str


class RunCodebaseConnectionInput(BaseModel):
    presigned_url: str
    provisional_codebase_name: str
    org_id: str
    version_id: str
    provider: str = "manual"


@hatchet.task(
    name="handle-github-events-workflow", execution_timeout=timedelta(minutes=60)
)
def handle_github_events_task(input: HandleGithubEventsInput, ctx: Context) -> None:
    print("starting handle github events task")
    handle_github_events(
        input.installation_id,
        input.org_id,
        input.repos_added,
        input.repos_deleted,
        input.repos_pushed,
    )
    print("executed handle github events task")


@hatchet.task(
    name="handle-gitlab-events-workflow", execution_timeout=timedelta(minutes=60)
)
def handle_gitlab_events_task(input: HandleGitlabEventsInput, ctx: Context) -> None:
    print("starting handle gitlab events task")
    handle_gitlab_events(
        input.installation_id,
        input.org_id,
        input.repos_added,
        input.repos_deleted,
        input.repos_pushed,
    )
    print("executed handle gitlab events task")


@hatchet.task(
    name="handle-bitbucket-events-workflow", execution_timeout=timedelta(minutes=60)
)
def handle_bitbucket_events_task(
    input: HandleBitbucketEventsInput, ctx: Context
) -> None:
    print("starting handle bitbucket events task")
    handle_bitbucket_events(
        input.installation_id,
        input.org_id,
        input.repos_added,
        input.repos_deleted,
        input.repos_pushed,
    )
    print("executed handle bitbucket events task")


@hatchet.task(
    name="handle-azure-devops-events-workflow", execution_timeout=timedelta(minutes=60)
)
def handle_azure_devops_events_task(
    input: HandleAzureDevopsEventsInput, ctx: Context
) -> None:
    print("starting handle azure devops events task")
    handle_azure_devops_events(
        input.installation_id,
        input.org_id,
        input.repos_added,
        input.repos_deleted,
        input.repos_pushed,
    )
    print("executed handle azure devops events task")


@hatchet.task(
    name="connect-repos-for-installation-workflow",
    execution_timeout=timedelta(minutes=60),
)
def connect_repos_for_installation_task(
    input: ConnectReposForInstallationInput, ctx: Context
) -> None:
    print("starting connect repos for installation task")
    connect_repos_for_installation(input.github_installation_id)
    print("executed connect repos for installation task")


@hatchet.task(
    name="run-codebase-connection-workflow", execution_timeout=timedelta(minutes=740)
)
def run_codebase_connection_task(
    input: RunCodebaseConnectionInput, ctx: Context
) -> None:
    print("starting run codebase connection task")
    run_codebase_connection(
        input.presigned_url,
        input.provisional_codebase_name,
        input.org_id,
        input.version_id,
        input.provider,
    )
    print("executed run codebase connection task")
