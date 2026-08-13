import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_cors_preflight_register():
    """Verify CORS OPTIONS preflight request on /api/v1/auth/register succeeds with correct headers."""
    client = TestClient(app, raise_server_exceptions=False)
    
    origins_to_test = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost",
        "http://127.0.0.1",
    ]
    
    for origin in origins_to_test:
        response = client.options(
            "/api/v1/auth/register",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 200, f"CORS preflight failed for origin {origin}: {response.text}"
        assert response.headers.get("access-control-allow-origin") == origin
        assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_preflight_login():
    """Verify CORS OPTIONS preflight request on /api/v1/auth/login succeeds."""
    client = TestClient(app, raise_server_exceptions=False)
    
    response = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") == "true"
