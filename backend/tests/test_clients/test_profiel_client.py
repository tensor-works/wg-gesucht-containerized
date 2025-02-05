import pytest
import os
import signal
import subprocess
import time
import requests
from pathlib import Path
from fastapi import HTTPException
from clients.profile_client import ProfileClient
from tests.logger import TestLogger

logger = TestLogger("ProfileClientTests")


@pytest.fixture(scope="session")
def wg_credentials():
    """Real WG-Gesucht credentials."""
    return {"email": "amadou.6e@googlemail.com", "password": "SomePassworFrSkrr"}


@pytest.fixture(scope="session")
def ensure_db_api():
    """Ensure database API is running."""
    api_url = "http://localhost:7999"
    api_process = None

    try:
        response = requests.get(f"{api_url}/health")
        if response.status_code == 200:
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
        if response.status_code == 200:
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
def ensure_profile_api(ensure_auth_api):
    """Ensure profile API is running."""
    api_url = "http://localhost:8001"
    api_process = None

    try:
        response = requests.get(f"{api_url}/health")
        if response.status_code == 200:
            yield api_url
            return
    except requests.RequestException:
        api_process = subprocess.Popen(["python", "-m", "api.v1.profile"], preexec_fn=os.setsid)
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
            pytest.fail("Profile API failed to start")

    yield api_url

    if api_process:
        os.killpg(os.getpgid(api_process.pid), signal.SIGTERM)


@pytest.fixture(scope="session")
def profile_client(ensure_profile_api) -> ProfileClient:
    """Create profile client instance."""
    return ProfileClient(ensure_profile_api)


@pytest.fixture(scope="session")
def authenticated_session(ensure_auth_api, wg_credentials) -> str:
    """Get authenticated session token."""
    response = requests.post(f"{ensure_auth_api}/authenticate/wg-gesucht", json=wg_credentials)
    assert response.status_code == 200
    return response.json()["session_token"]


def test_health_check(profile_client):
    """Test health check endpoint."""
    result = profile_client.health_check()
    assert result["status"] == "healthy"
    assert result["profile_service"] == "operational"


def test_get_profile_photo(profile_client, authenticated_session):
    """Test profile photo retrieval."""
    photo_url = profile_client.get_profile_photo(authenticated_session)
    assert photo_url.startswith("https://")
    assert ".jpg" in photo_url.lower() or ".png" in photo_url.lower()


def test_get_profile_name(profile_client, authenticated_session):
    """Test profile name retrieval."""
    name_data = profile_client.get_profile_name(authenticated_session)
    assert "first_name" in name_data
    assert "last_name" in name_data
    assert len(name_data["first_name"]) > 0
    assert len(name_data["last_name"]) > 0


def test_get_profile_address(profile_client, authenticated_session):
    """Test profile address retrieval."""
    address_data = profile_client.get_profile_address(authenticated_session)
    assert "city" in address_data
    assert "postal_code" in address_data
    assert "street_and_house_number" in address_data


def test_download_profile_photo(profile_client, authenticated_session):
    """Test profile photo download."""
    photo_path = profile_client.download_profile_photo(authenticated_session)
    assert os.path.exists(photo_path)
    os.remove(photo_path)


def test_invalid_session(profile_client):
    """Test client with invalid session token."""
    with pytest.raises(HTTPException) as exc_info:
        profile_client.get_profile_photo("invalid-token")
    assert exc_info.value.status_code == 401

    with pytest.raises(HTTPException) as exc_info:
        profile_client.get_profile_name("invalid-token")
    assert exc_info.value.status_code == 401

    with pytest.raises(HTTPException) as exc_info:
        profile_client.get_profile_address("invalid-token")
    assert exc_info.value.status_code == 401

    with pytest.raises(HTTPException) as exc_info:
        profile_client.download_profile_photo("invalid-token")
    assert exc_info.value.status_code == 401


def test_connection_error(profile_client):
    """Test handling of connection errors."""
    bad_client = ProfileClient("http://localhost:9999")

    with pytest.raises(HTTPException) as exc_info:
        bad_client.health_check()
    assert exc_info.value.status_code == 500
    assert "failed" in str(exc_info.value.detail)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
