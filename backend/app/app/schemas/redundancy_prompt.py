from pydantic import BaseModel


class RedundancyPromptBase(BaseModel):
    pass


class RedundancyPromptCreate(RedundancyPromptBase):
    issue_id: str
    current_article_id: str
    previous_article_id: str
    response: bool


class RedundancyPromptUpdate(RedundancyPromptBase):
    pass
