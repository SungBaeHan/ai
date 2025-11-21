# tests/test_cors.py
"""
CORS 설정 테스트 예시

실제로 Access-Control-Allow-Origin 헤더가 응답에 포함되는지 확인하는 테스트

사용 예시:
    # pytest로 실행
    pytest tests/test_cors.py -v
    
    # 또는 직접 실행
    python -m pytest tests/test_cors.py::test_cors_headers -v
"""

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app


@pytest.fixture
def client():
    """테스트용 FastAPI 클라이언트"""
    return TestClient(app)


def test_cors_headers(client):
    """CORS 헤더가 올바르게 설정되었는지 확인"""
    # 허용된 origin으로 요청
    origin = "https://arcanaverse.ai"
    
    response = client.get(
        "/health",
        headers={"Origin": origin}
    )
    
    # 응답이 성공하는지 확인
    assert response.status_code == 200
    
    # CORS 헤더 확인
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == origin
    
    # 다른 CORS 헤더도 확인
    assert "access-control-allow-credentials" in response.headers
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_preflight(client):
    """OPTIONS 요청(Preflight)이 올바르게 처리되는지 확인"""
    origin = "https://arcanaverse.ai"
    
    response = client.options(
        "/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        }
    )
    
    # Preflight 응답 확인
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == origin
    assert "access-control-allow-methods" in response.headers


def test_cors_blocked_origin(client):
    """허용되지 않은 origin은 차단되는지 확인"""
    # 허용되지 않은 origin
    origin = "https://evil.com"
    
    response = client.get(
        "/health",
        headers={"Origin": origin}
    )
    
    # 응답은 성공하지만 CORS 헤더가 없거나 다른 origin이어야 함
    assert response.status_code == 200
    # 허용되지 않은 origin이면 CORS 헤더가 없거나 다른 값이어야 함
    if "access-control-allow-origin" in response.headers:
        assert response.headers["access-control-allow-origin"] != origin

