from typing import TypedDict, Optional


class PipelineState(TypedDict):
    owner: str
    repo: str
    issue_number: int
    issue_title: str
    issue_body: str
    requirements: Optional[dict]
    investigation: Optional[dict]
    fix: Optional[dict]
    needs_human_approval: bool
    status: str