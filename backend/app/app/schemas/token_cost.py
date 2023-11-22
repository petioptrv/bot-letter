from app.base_types import Model


class TokenCostBase(Model):
    pass


class TokenCostCreate(TokenCostBase):
    issue_id: str
    article_id: str
    action: str
    input_tokens: int
    output_tokens: int


class TokenCostUpdate(TokenCostBase):
    pass
