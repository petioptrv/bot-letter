from pydantic import BaseModel


class TokenCostBase(BaseModel):
    pass


class TokenCostCreate(TokenCostBase):
    issue_id: str
    article_id: str
    action: str
    input_tokens: int
    output_tokens: int


class TokenCostUpdate(TokenCostBase):
    pass
