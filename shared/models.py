from pydantic import BaseModel, field_validator
from typing import Optional


class IncomingMessage(BaseModel):
    platform: str
    user_id: str
    message_id: Optional[int] = None
    text: str
    lang: Optional[str] = 'en'

    @field_validator('user_id', mode='before')
    @classmethod
    def coerce_user_id(cls, v):
        return str(v)


class OutgoingMessage(BaseModel):
    platform: str
    user_id: str
    text: str
    lang: str

    @field_validator('user_id', mode='before')
    @classmethod
    def coerce_user_id(cls, v):
        return str(v)
