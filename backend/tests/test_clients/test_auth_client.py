import pytest
import os
import subprocess
import signal
import time
import requests
from pathlib import Path
from fastapi import HTTPException
from clients.auth_client import AuthClient
from tests.logger import TestLogger

logger = TestLogger("AuthClientTests")


@pytest.fixture(scope="session")
def openai_credentials():
    """OpenAI credentials from environment."""
    return {"api_key": os.getenv("OPENAI_API_KEY", "dummy-key")}


@pytest.fixture(scope="session")
def wg_credentials() -> dict:
    """Real WG-Gesucht credentials that work."""
    return {
        "email": "amadou.6e@googlemail.com",
        "password": "SomePassworFrSkrr",
    }


@pytest.fixture(scope="session")
def ensure_db_api():
    """Ensure database API is running and healthy."""
    api_url = "http://localhost:7999"
    api_process = None

    try:
        # First try to connect to existing service
        response = requests.get(f"{api_url}/health")
        if response.status_code == 200 and response.json().get("status") == "healthy":
            yield api_url
            return
    except requests.RequestException:
        # API not running, start it
        api_process = subprocess.Popen([
            "python",
            "-m",
            "api.v1.database",
        ], preexec_fn=os.setsid)

        # Wait for API to start (up to 5 seconds)
        for _ in range(10):
            try:
                response = requests.get(f"{api_url}/health")
                if response.status_code == 200 and response.json().get("status") == "healthy":
                    break
            except requests.RequestException:
                time.sleep(0.5)
        else:
            if api_process:
                os.killpg(os.getpgid(api_process.pid), signal.SIGTERM)
            pytest.fail("Database API failed to start")

    yield api_url

    # Cleanup: Stop the API if we started it
    if api_process:
        os.killpg(os.getpgid(api_process.pid), signal.SIGTERM)


@pytest.fixture(scope="session")
def ensure_auth_api(ensure_db_api):
    """Ensure authentication API is running and healthy."""
    api_url = "http://localhost:8000"
    api_process = None

    try:
        # First try to connect to existing service
        response = requests.get(f"{api_url}/health")
        if response.status_code == 200 and response.json().get("status") == "healthy":
            yield api_url
            return
    except requests.RequestException:
        # API not running, start it
        api_process = subprocess.Popen([
            "python",
            "-m",
            "api.v1.auth",
        ], preexec_fn=os.setsid)

        # Wait for API to start (up to 5 seconds)
        for _ in range(10):
            try:
                response = requests.get(f"{api_url}/health")
                if response.status_code == 200 and response.json().get("status") == "healthy":
                    break
            except requests.RequestException:
                time.sleep(0.5)
        else:
            if api_process:
                os.killpg(os.getpgid(api_process.pid), signal.SIGTERM)
            pytest.fail("Auth API failed to start")

    yield api_url

    # Cleanup: Stop the API if we started it
    if api_process:
        os.killpg(os.getpgid(api_process.pid), signal.SIGTERM)


@pytest.fixture(scope="session")
def auth_client(ensure_auth_api: str) -> AuthClient:
    """Create auth client instance."""
    return AuthClient(ensure_auth_api)


@pytest.fixture
def authenticated_session(auth_client: AuthClient, wg_credentials: dict) -> str:
    """Get an authenticated session token."""
    response = auth_client.authenticate_wg_gesucht(
        wg_credentials["email"],
        wg_credentials["password"],
    )
    return response["session_token"]


def test_health_check(auth_client: AuthClient):
    """Test health check endpoint."""
    logger.info("Testing health check")

    result = auth_client.health_check()
    assert result["status"] == "healthy"
    assert result["auth_service"] == "operational"


def test_wg_gesucht_authentication(
    auth_client: AuthClient,
    wg_credentials: dict,
):
    """Test WG-Gesucht authentication."""
    logger.info("Testing WG-Gesucht authentication")

    result = auth_client.authenticate_wg_gesucht(
        wg_credentials["email"],
        wg_credentials["password"],
    )
    assert "session_token" in result
    assert len(result["session_token"]) > 0

    # Test token validation
    is_valid = auth_client.validate_session_token(result["session_token"])
    assert is_valid is True


def test_wg_gesucht_authentication_failure(auth_client: AuthClient):
    """Test WG-Gesucht authentication failure."""
    logger.info("Testing WG-Gesucht authentication failure")

    with pytest.raises(HTTPException) as exc_info:
        auth_client.authenticate_wg_gesucht(
            "wrong@email.com",
            "wrongpass",
        )
    assert exc_info.value.status_code == 401
    assert "invalid wg-gesucht credentials" in str(exc_info.value.detail).lower()


def test_openai_authentication(
    auth_client: AuthClient,
    authenticated_session: str,
    openai_credentials: dict,
):
    """Test OpenAI authentication."""
    logger.info("Testing OpenAI authentication")

    result = auth_client.authenticate_openai(
        authenticated_session,
        openai_credentials["api_key"],
    )
    assert result["message"] == "Successfully stored OpenAI API key"

    # Verify credentials are stored
    credentials = auth_client.get_credentials(authenticated_session)
    assert "openai_key" in credentials
    assert credentials["openai_key"] == openai_credentials["api_key"]


def test_openai_authentication_invalid_token(
    auth_client: AuthClient,
    openai_credentials: dict,
):
    """Test OpenAI authentication with invalid session token."""
    logger.info("Testing OpenAI authentication with invalid token")

    with pytest.raises(HTTPException) as exc_info:
        auth_client.authenticate_openai(
            "invalid-token",
            openai_credentials["api_key"],
        )
    assert exc_info.value.status_code == 401
    assert "invalid session token" in str(exc_info.value.detail).lower()


def test_token_validation(
    auth_client: AuthClient,
    authenticated_session: str,
):
    """Test token validation."""
    logger.info("Testing token validation")

    # Test valid token
    is_valid = auth_client.validate_session_token(authenticated_session)
    assert is_valid is True

    # Test invalid token
    is_valid = auth_client.validate_session_token("invalid-token")
    assert is_valid is False


def test_get_credentials(auth_client: AuthClient, authenticated_session: str):
    """Test retrieving stored credentials."""
    logger.info("Testing credential retriefval")

    credentials = auth_client.get_credentials(authenticated_session)
    assert isinstance(credentials, dict)
    assert "wg_password" in credentials
    assert credentials["email"] is not None


def test_get_credentials_invalid_token(auth_client: AuthClient):
    """Test retrieving credentials with invalid token."""
    logger.info("Testing credential retrieval with invalid token")

    with pytest.raises(HTTPException) as exc_info:
        auth_client.get_credentials("invalid-token")
    assert exc_info.value.status_code == 401
    assert "invalid session token" in str(exc_info.value.detail).lower()


def test_delete_credentials(auth_client: AuthClient, authenticated_session: str,
                            openai_credentials: dict):
    """Test deleting stored credentials."""
    logger.info("Testing credential deletion")

    # First store OpenAI credentials
    auth_client.authenticate_openai(
        authenticated_session,
        openai_credentials["api_key"],
    )

    # Delete OpenAI credentials
    result = auth_client.delete_credentials(authenticated_session, "openai")
    assert result["message"] == "Credentials deleted successfully"

    # Verify deletion
    credentials = auth_client.get_credentials(authenticated_session)
    assert "openai" not in credentials


def test_delete_credentials_invalid_token(auth_client: AuthClient):
    """Test deleting credentials with invalid token."""
    logger.info("Testing credential deletion with invalid token")

    with pytest.raises(HTTPException) as exc_info:
        auth_client.delete_credentials("invalid-token", "openai")
    assert exc_info.value.status_code == 401
    assert "invalid session token" in str(exc_info.value.detail).lower()


def test_connection_error_handling(auth_client: AuthClient):
    """Test handling of connection errors."""
    logger.info("Testing connection error handling")

    # Test with unreachable server
    bad_client = AuthClient("http://localhost:9999")
    with pytest.raises(HTTPException) as exc_info:
        bad_client.health_check()
    assert exc_info.value.status_code == 500
    assert "failed" in str(exc_info.value.detail).lower()


if __name__ == "__main__":
    pytest.main(["-v", __file__])
