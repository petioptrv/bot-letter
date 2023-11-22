from pydantic import BaseModel


class IssueArticleBase(BaseModel):
    issue_id: str
    article_id: str


class IssueArticleCreate(IssueArticleBase):
    issue_id: str
    article_id: str


class IssueArticleUpdate(IssueArticleBase):
    pass
