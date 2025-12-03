from __future__ import annotations

from pydantic import BaseModel


class SessionValidateRequest(BaseModel):
    token: str


class SessionValidateResponse(BaseModel):
    ok: bool = True
    user_id: str
    display_name: str
    member_level: int
    is_use: bool
    is_lock: bool

