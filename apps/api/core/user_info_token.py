from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from pydantic import BaseModel, EmailStr

from apps.api.config import settings


class UserInfoTokenPayload(BaseModel):
    user_id: str
    email: EmailStr
    display_name: str
    member_level: int
    last_login_at: datetime
    expired_at: datetime
    issued_at: datetime
    version: int = 1


def _get_fernet() -> Fernet:
    # Fernet key 는 32 bytes 를 base64-url 로 인코딩한 값이어야 해서,
    # 우리가 넣은 시크릿 문자열에서 안전하게 파생시킨다.
    key_bytes = hashlib.sha256(settings.AUTH_USER_INFO_V2_SECRET.encode("utf-8")).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(fernet_key)


def create_user_info_token(
    *,
    user_id: str,
    email: str,
    display_name: str,
    member_level: int,
    last_login_at: datetime | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    if last_login_at is None:
        last_login_at = now

    expired_at = now + timedelta(minutes=settings.AUTH_USER_INFO_V2_EXPIRE_MINUTES)

    payload = UserInfoTokenPayload(
        user_id=user_id,
        email=email,
        display_name=display_name,
        member_level=member_level,
        last_login_at=last_login_at,
        expired_at=expired_at,
        issued_at=now,
    )

    f = _get_fernet()
    json_bytes = json.dumps(
        payload.model_dump(mode="json", by_alias=True),
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    token = f.encrypt(json_bytes)
    return token.decode("utf-8")


def decode_user_info_token(token: str) -> UserInfoTokenPayload:
    f = _get_fernet()
    try:
        data = f.decrypt(token.encode("utf-8"))
    except InvalidToken:
        raise ValueError("invalid_user_info_v2_token")

    obj: dict[str, Any] = json.loads(data.decode("utf-8"))
    return UserInfoTokenPayload.model_validate(obj)

