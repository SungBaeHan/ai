# apps/api/deps/user_snapshot.py
"""
게임 세션에 저장할 유저 스냅샷 생성 헬퍼
"""

from typing import Any, Dict


def build_owner_ref_info(current_user: Dict[str, Any]) -> Dict[str, Any]:
    """
    game_session 문서에 저장할 owner_ref_info 스냅샷을 생성한다.
    current_user는 /auth/validate-session 토큰을 디코딩한 결과 또는
    get_current_user_v2가 반환하는 dict 형태라는 전제로 구성.
    
    Args:
        current_user: 사용자 정보 딕셔너리
            - user_id: str
            - email: str
            - display_name: str
            - member_level: int (optional)
            - is_use: str or bool ("Y"/"N" or True/False)
            - is_lock: str or bool ("Y"/"N" or True/False)
            - last_login_at: datetime (optional)
    
    Returns:
        owner_ref_info 딕셔너리
    """
    # is_use, is_lock을 boolean으로 변환
    is_use = current_user.get("is_use", True)
    if isinstance(is_use, str):
        is_use = is_use == "Y"
    
    is_lock = current_user.get("is_lock", False)
    if isinstance(is_lock, str):
        is_lock = is_lock == "Y"
    
    return {
        "user_ref_id": current_user.get("user_id"),
        "email": current_user.get("email"),
        "display_name": current_user.get("display_name"),
        "member_level": current_user.get("member_level", 1),
        "is_use": is_use,
        "is_lock": is_lock,
        "last_login_at": current_user.get("last_login_at"),
    }
