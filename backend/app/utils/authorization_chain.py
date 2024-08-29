from typing import Callable, List
from fastapi import HTTPException
from sqlmodel import Session

class AuthorizationChain:
    def __init__(self, session: Session):
        self.session = session
        self.checks: List[Callable[[Session], bool]] = []

    def add_check(self, check: Callable[[Session], bool]) -> 'AuthorizationChain':
        self.checks.append(check)
        return self

    def execute(self):
        for check in self.checks:
            if not check(self.session):
                raise HTTPException(status_code=403, detail="Authorization failed")
        return True
    



def perform_authorization_checks(session: Session, checks: List[Callable[[Session], bool]]):
    checker = AuthorizationChain(session)
    for check in checks:
        checker.add_check(check)
    checker.execute()    