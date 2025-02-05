import pytest
import os
import signal
import subprocess
import time
import requests
from pathlib import Path
from fastapi.testclient import TestClient
from api.v1.profile import app
from services.profile_service import ProfileService
from utils.browser_manager import BrowserManager
from tests.logger import TestLogger

logger = TestLogger("ProfileAPITests")


@pytest.fixture(scope="session")
def wg_credentials():
    """Real WG-Gesucht credentials that work."""
    return {"email": "amadou.6e@googlemail.com", "password": "SomePassworFrSkrr"}


@pytest.fixture(scope="session")
def ensure_db_api():
    """Ensure database API is running."""
    api_url = "http://localhost:7999"
    api_process = None

    try:
        response = requests.get(f"{api_url}/health")
        if response.status_code == 200 and response.json().get("status") == "healthy":
            yield api_url
            return
    except requests.RequestException:
        api_process = subprocess.Popen(["python", "-m", "api.v1.database"], preexec_fn=os.setsid)
        for _ in range(10):
            try:
                response = requests.get(f"{api_url}/health")
                if response.status_code == 200:
                    break
            except requests.RequestException:
                time.sleep(0.5)
        else:
            if api_process:
                os.killpg(os.getpgid(api_process.pid), signal.SIGTERM)
            pytest.fail("Database API failed to start")

    yield api_url

    if api_process:
        os.killpg(os.getpgid(api_process.pid), signal.SIGTERM)


@pytest.fixture(scope="session")
def ensure_auth_api(ensure_db_api):
    """Ensure auth API is running."""
    api_url = "http://localhost:8000"
    api_process = None

    try:
        response = requests.get(f"{api_url}/health")
        if response.status_code == 200 and response.json().get("status") == "healthy":
            yield api_url
            return
    except requests.RequestException:
        api_process = subprocess.Popen(["python", "-m", "api.v1.auth"], preexec_fn=os.setsid)
        for _ in range(10):
            try:
                response = requests.get(f"{api_url}/health")
                if response.status_code == 200:
                    break
            except requests.RequestException:
                time.sleep(0.5)
        else:
            if api_process:
                os.killpg(os.getpgid(api_process.pid), signal.SIGTERM)
            pytest.fail("Auth API failed to start")

    yield api_url

    if api_process:
        os.killpg(os.getpgid(api_process.pid), signal.SIGTERM)


@pytest.fixture(scope="session")
def test_client():
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture(scope="module")
def authenticated_session(ensure_auth_api: str, wg_credentials: dict) -> str:
    """Get authenticated session for testing."""
    response = requests.post(f"{ensure_auth_api}/authenticate/wg-gesucht", json=wg_credentials)
    assert response.status_code == 200
    return response.json()["session_token"]


@pytest.fixture(scope="module")
def cleanup_database(ensure_db_api):
    """Clean test data from database."""
    requests.post(f"{ensure_db_api}/query",
                  json={"query": "DELETE FROM users WHERE email = 'amadou.6e@googlemail.com'"})
    yield
    requests.post(f"{ensure_db_api}/query",
                  json={"query": "DELETE FROM users WHERE email = 'amadou.6e@googlemail.com'"})


def test_health_check(test_client: TestClient):
    """Test health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["profile_service"] == "operational"


def test_get_profile_photo(test_client: TestClient, authenticated_session: str):
    """Test profile photo retrieval."""
    response = test_client.get("/profile/photo", params={"session_token": authenticated_session})
    assert response.status_code == 200
    data = response.json()
    assert "photo_url" in data
    assert data["photo_url"].startswith("https://")


def test_get_profile_name(test_client: TestClient, authenticated_session: str):
    """Test profile name retrieval."""
    response = test_client.get("/profile/name", params={"session_token": authenticated_session})
    assert response.status_code == 200
    data = response.json()
    assert "first_name" in data
    assert "last_name" in data
    assert len(data["first_name"]) > 0
    assert len(data["last_name"]) > 0


def test_get_profile_address(test_client: TestClient, authenticated_session: str):
    """Test profile address retrieval."""
    response = test_client.get("/profile/address", params={"session_token": authenticated_session})
    assert response.status_code == 200
    data = response.json()
    assert "city" in data
    assert "postal_code" in data
    assert "street_and_house_number" in data


def test_download_profile_photo(test_client: TestClient, authenticated_session: str):
    """Test profile photo download."""
    response = test_client.post(
        "/profile/photo/download",
        params={"session_token": authenticated_session},
    )
    assert response.status_code == 200
    data = response.json()
    assert "photo_path" in data
    assert os.path.exists(data["photo_path"])
    os.remove(data["photo_path"])


def test_invalid_session(test_client: TestClient):
    """Test endpoints with invalid session token."""
    endpoints = [
        ("/profile/photo", "get"),
        ("/profile/name", "get"),
        ("/profile/address", "get"),
        ("/profile/photo/download", "post"),
    ]

    for endpoint, method in endpoints:
        if method == "get":
            response = test_client.get(endpoint, params={"session_token": "invalid"})
        else:
            response = test_client.post(endpoint, params={"session_token": "invalid"})
        assert response.status_code == 401


def test_error_handling(test_client: TestClient, authenticated_session: str):
    """Test error handling for invalid paths."""
    response = test_client.get("/invalid/path")
    assert response.status_code == 404

    response = test_client.post(
        "/profile/photo/download",
        params={
            "session_token": authenticated_session,
            "save_path": "/invalid/path/photo.jpg"
        },
    )
    assert response.status_code == 500


if __name__ == "__main__":
    pytest.main(["-v", __file__])
