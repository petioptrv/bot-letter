from pydantic import BaseModel


class RelevancyPromptBase(BaseModel):
    pass


class RelevancyPromptCreate(RelevancyPromptBase):
    issue_id: str
    article_id: str
    response: bool


class RelevancyPromptUpdate(RelevancyPromptBase):
    pass
