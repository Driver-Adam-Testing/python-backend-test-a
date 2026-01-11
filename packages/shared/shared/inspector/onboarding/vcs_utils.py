from pydantic import BaseModel


class AuthorInfo(BaseModel):
    email: str
    name: str
    date: str


class CommitInfo(BaseModel):
    sha: str
    message: str
    url: str
    author: AuthorInfo


class BranchInfo(BaseModel):
    name: str


class RepoInfo(BaseModel):
    name: str
    namespace: str
    full_name: str
    url: str


class VersionControlInfo(BaseModel):
    repository: RepoInfo
    commit: CommitInfo
    branch: BranchInfo
