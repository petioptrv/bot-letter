from app.base_types import Model


class IssueArticleBase(Model):
    issue_id: str
    article_id: str


class IssueArticleCreate(IssueArticleBase):
    issue_id: str
    article_id: str


class IssueArticleUpdate(IssueArticleBase):
    pass
