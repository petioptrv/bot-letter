from typing import Optional

from app.base_types import Model


class Token(Model):
    access_token: str
    token_type: str


class TokenPayload(Model):
    sub: Optional[int] = None
