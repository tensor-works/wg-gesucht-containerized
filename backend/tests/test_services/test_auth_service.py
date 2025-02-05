import pytest
import os
import requests
import subprocess
import signal
import time
from pathlib import Path
from utils import getenv
from fastapi import HTTPException
from services.auth_service import AuthService, OpenAICredentials
from services.database_service import DatabaseService, DBConfig
from utils.browser_manager import BrowserManager


@pytest.fixture(scope="session")
def wg_credentials() -> dict:
    """Real WG-Gesucht credentials that work."""
    return {
        "email": "amadou.6e@googlemail.com",
        "password": "SomePassworFrSkrr",
    }


@pytest.fixture(scope="session")
def db_config() -> DBConfig:
    """Database configuration using environment variables."""
    return DBConfig(
        host="localhost",
        port=5432,
        database="postgres",
        user=os.getenv("POSTGRES_ROLE"),
        password=os.getenv("POSTGRES_PWD"),
    )


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
def db_service(db_config) -> DatabaseService:
    """Create database service instance."""
    return DatabaseService(db_config)


@pytest.fixture(scope="session")
def browser_manager() -> BrowserManager:
    """Create browser manager instance."""
    return BrowserManager()


@pytest.fixture(scope="function")
def auth_service(
    browser_manager: BrowserManager,
    ensure_db_api: str,
) -> AuthService:
    """Create auth service instance with database API."""
    return AuthService(
        browser_manager=browser_manager,
        db_api_url=ensure_db_api,
    )


@pytest.fixture(autouse=True)
def cleanup_database(db_service: DatabaseService):
    """Clean up test data from database before and after tests."""
    # Clean up before test
    db_service.execute_query(
        "DELETE FROM sessions WHERE user_id IN (SELECT id::text FROM users WHERE email = 'amadou.6e@googlemail.com')"
    )
    db_service.execute_query("DELETE FROM users WHERE email = 'amadou.6e@googlemail.com'")
    db_service.execute_query("DELETE FROM users WHERE email = 'invalid@example.com'")
    yield
    # Clean up after test
    db_service.execute_query(
        "DELETE FROM sessions WHERE user_id IN (SELECT id::text FROM users WHERE email = 'amadou.6e@googlemail.com')"
    )
    db_service.execute_query("DELETE FROM users WHERE email = 'amadou.6e@googlemail.com'")
    db_service.execute_query("DELETE FROM users WHERE email = 'invalid@example.com'")


@pytest.fixture(autouse=True)
def cleanup_vault_files():
    """Clean up vault files before and after tests using os.system."""
    vault_dir = Path(os.getenv("WORKINGDIR", "."), "data", "users")

    if vault_dir.exists():
        os.system(f"rm -rf {vault_dir}")

    yield

    if vault_dir.exists():
        os.system(f"rm -rf {vault_dir}")


def test_wg_gesucht_authentication_flow(
    auth_service: AuthService,
    wg_credentials: dict,
    ensure_db_api: str,
    db_service: DatabaseService,
):
    """Test complete WG-Gesucht authentication flow with real credentials."""
    # Authenticate with WG-Gesucht
    response = auth_service.authenticate_wg_gesucht(wg_credentials)

    assert response.message == "Successfully authenticated with WG-Gesucht"
    assert response.user_id is not None
    assert response.session_token is not None

    # Verify user was created in database
    user_result = db_service.select(
        "users",
        conditions=f"email = '{wg_credentials['email']}'",
    )
    assert user_result["success"]
    assert len(user_result["data"]) == 1

    # Verify session was created
    session_result = db_service.select(
        "sessions",
        conditions=f"user_id = '{response.user_id}'",
    )
    assert session_result["success"]
    assert len(session_result["data"]) == 1

    # Verify credentials were stored in vault
    vault = auth_service._get_user_vault(response.user_id)
    stored_password = vault.get_secret("wg_password")
    assert stored_password == wg_credentials["password"]


def test_wg_gesucht_authentication_invalid_credentials(
    auth_service: AuthService,
    db_service: DatabaseService,
):
    """Test WG-Gesucht authentication with invalid credentials."""

    # Define invalid credentials
    invalid_credentials = {"email": "invalid@example.com", "password": "wrongpassword"}

    # Try authenticating with invalid credentials
    with pytest.raises(HTTPException) as exc_info:
        auth_service.authenticate_wg_gesucht(invalid_credentials)

    # Assert that the error is a 401 Unauthorized
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid WG-Gesucht credentials"

    # Ensure no user was created in the database
    user_result = db_service.select(
        "users",
        conditions=f"email = '{invalid_credentials['email']}'",
    )
    assert user_result["success"]
    assert len(user_result["data"]) == 0

    # Ensure no session was created
    session_result = db_service.select(
        "sessions",
        conditions=f"user_id = '{invalid_credentials['email']}'",
    )
    assert session_result["success"]
    assert len(session_result["data"]) == 0


def test_openai_integration(
    auth_service: AuthService,
    wg_credentials: dict,
):
    """Test OpenAI integration after WG-Gesucht authentication."""
    # First authenticate with WG-Gesucht
    wg_response = auth_service.authenticate_wg_gesucht(wg_credentials)

    # Test with invalid OpenAI key
    invalid_key = "sk-invalid123"
    with pytest.raises(HTTPException) as exc:
        auth_service.authenticate_openai(
            wg_response.session_token,
            OpenAICredentials(api_key=invalid_key),
        )
    assert exc.value.status_code == 401
    assert "Invalid OpenAI API key" in str(exc.value.detail)

    # Test with valid OpenAI key (if available)
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        response = auth_service.authenticate_openai(
            wg_response.session_token,
            OpenAICredentials(api_key=openai_key),
        )
        assert response.message == "Successfully stored OpenAI API key"

        # Verify OpenAI key storage
        vault = auth_service._get_user_vault(wg_response.user_id)
        stored_key = vault.get_secret("openai_key")
        assert stored_key == openai_key


def test_credential_retrieval(
    auth_service: AuthService,
    wg_credentials: dict,
):
    """Test retrieving stored credentials."""
    # Set up authentication first
    wg_response = auth_service.authenticate_wg_gesucht(wg_credentials,)

    # Add OpenAI key if available
    openai_key = getenv("OPENAI_API_KEY")
    openai_response = auth_service.authenticate_openai(
        wg_response.session_token,
        OpenAICredentials(api_key=openai_key),
    )

    # Retrieve credentials
    stored_creds = auth_service.get_credentials(wg_response.session_token,)

    # Verify retrieved credentials
    assert stored_creds["email"] == wg_credentials["email"]
    assert stored_creds["wg_password"] == wg_credentials["password"]
    if openai_key:
        assert stored_creds["openai_key"] == openai_key


def test_session_management(
    auth_service: AuthService,
    wg_credentials: dict,
    db_service: DatabaseService,
):
    """Test session token management and validation."""
    # test random token
    assert auth_service.validate_session_token("invalid-token") is False

    # Create initial session
    response1 = auth_service.authenticate_wg_gesucht(wg_credentials,)
    token1 = response1.session_token

    # Validate the token
    assert auth_service.validate_session_token(token1) is True
    assert auth_service.get_user_id(token1) == response1.user_id

    # Create second session
    response2 = auth_service.authenticate_wg_gesucht(wg_credentials)
    token2 = response2.session_token

    # Verify tokens are different but valid
    assert token1 != token2
    assert auth_service.validate_session_token(token2) is True
    assert auth_service.get_user_id(token2) == response2.user_id

    # Verify both sessions exist in database
    sessions = db_service.select(
        "sessions",
        conditions=f"user_id = '{response1.user_id}'",
    )
    assert len(sessions["data"]) == 2


if __name__ == "__main__":
    pytest.main(["-v", __file__])
