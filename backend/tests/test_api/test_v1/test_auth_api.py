import pytest
import os
import requests
import signal
import subprocess
import time
from services.database_service import DBConfig
from fastapi.testclient import TestClient
from api.v1.auth import app
from typing import Dict
from pathlib import Path
from utils import getenv


@pytest.fixture(scope="session")
def test_client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(scope="session")
def wg_credentials():
    """Real WG-Gesucht credentials that work."""
    return {"email": "amadou.6e@googlemail.com", "password": "SomePassworFrSkrr"}


@pytest.fixture(scope="session")
def openai_credentials():
    """OpenAI credentials from environment."""
    return {"api_key": os.getenv("OPENAI_API_KEY", "dummy-key")}


@pytest.fixture(autouse=True)
def cleanup_vault_files():
    """Clean up vault files before and after tests."""
    vault_dir = Path(os.getenv("WORKINGDIR", "."), "data", "users")
    if vault_dir.exists():
        os.system(f"rm -rf {vault_dir}")
    yield
    if vault_dir.exists():
        os.system(f"rm -rf {vault_dir}")


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


def test_health_check(test_client: TestClient) -> None:
    """Test the health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["auth_service"] == "operational"


def authenticate(
    test_client: TestClient,
    wg_credentials: Dict[str, str],
    ensure_db_api: str,
) -> str:
    """Test the WG-Gesucht authentication endpoint."""
    response = test_client.post(
        "/authenticate/wg-gesucht",
        json=wg_credentials,
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "session_token" in data
    assert "user_id" in data

    return data["session_token"]  # Return for use in other tests


def test_wg_gesucht_authentication_flow(
    test_client: TestClient,
    wg_credentials: Dict[str, str],
    ensure_db_api: str,
):
    authenticate(
        test_client,
        wg_credentials,
        ensure_db_api,
    )


def test_openai_authentication(
    test_client: TestClient,
    openai_credentials: Dict[str, str],
    wg_credentials: Dict[str, str],
    ensure_db_api: str,
) -> None:
    """Test the OpenAI authentication endpoint."""
    # First get a valid session token
    session_token = authenticate(
        test_client,
        wg_credentials,
        ensure_db_api,
    )

    # Test with invalid key
    invalid_response = test_client.post(
        "/authenticate/openai",
        params={"session_token": session_token},
        json={"api_key": "invalid-key"},
    )
    assert invalid_response.status_code == 401

    # Test with valid key
    if os.getenv("OPENAI_API_KEY"):
        valid_response = test_client.post(
            "/authenticate/openai",
            params={"session_token": session_token},
            json=openai_credentials,
        )
        assert valid_response.status_code == 200
        data = valid_response.json()
        assert data["message"] == "Successfully stored OpenAI API key"


def test_validate_token(
    test_client: TestClient,
    wg_credentials: Dict[str, str],
    ensure_db_api: str,
) -> None:
    """Test the token validation endpoint."""
    # Get a valid token
    session_token = authenticate(
        test_client,
        wg_credentials,
        ensure_db_api,
    )

    # Test valid token
    valid_response = test_client.get("/validate-token", params={"session_token": session_token})
    assert valid_response.status_code == 200
    assert valid_response.json()["valid"] is True

    # Test invalid token
    invalid_response = test_client.get("/validate-token", params={"session_token": "invalid-token"})
    assert invalid_response.status_code == 401


def test_get_credentials(
    test_client: TestClient,
    wg_credentials: Dict[str, str],
    ensure_db_api: str,
) -> None:
    """Test the credential retrieval endpoint."""
    # First authenticate to get a token
    session_token = authenticate(
        test_client,
        wg_credentials,
        ensure_db_api,
    )

    # Get credentials
    response = test_client.get("/get-credentials", params={"session_token": session_token})
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert "wg_password" in data
    assert data["email"] == wg_credentials["email"]
    assert data["wg_password"] == wg_credentials["password"]


def test_delete_credentials(
    test_client: TestClient,
    wg_credentials: Dict[str, str],
    openai_credentials: dict,
    ensure_db_api: str,
) -> None:
    """Test the credential deletion endpoint."""
    # First authenticate and store OpenAI key
    session_token = authenticate(
        test_client,
        wg_credentials,
        ensure_db_api,
    )
    getenv("OPENAI_API_KEY")
    test_client.post(
        "/authenticate/openai",
        params={"session_token": session_token},
        json=openai_credentials,
    )

    creds_response = test_client.get("/get-credentials", params={"session_token": session_token})
    assert creds_response.json()["openai_key"] is not None

    # Delete OpenAI key
    response = test_client.delete(
        "/delete-credentials",
        params={
            "session_token": session_token,
            "key": "openai_key"
        },
    )
    assert response.status_code == 200

    # Verify key is deleted
    creds_response = test_client.get("/get-credentials", params={"session_token": session_token})
    assert creds_response.json()["openai_key"] is None


def test_error_handling(
    test_client: TestClient,
    wg_credentials: Dict[str, str],
    ensure_db_api: str,
) -> None:
    """Test error handling for various scenarios."""
    # Test invalid WG-Gesucht credentials
    invalid_creds_response = test_client.post(
        "/authenticate/wg-gesucht",
        json={
            "email": "invalid@email.com",
            "password": "wrongpass"
        },
    )
    assert invalid_creds_response.status_code in (401, 500)

    # Test invalid session token
    invalid_token_response = test_client.get(
        "/get-credentials",
        params={"session_token": "invalid-token"},
    )
    assert invalid_token_response.status_code == 401

    # Test deleting non-existent credential
    invalid_delete_response = test_client.delete(
        "/delete-credentials",
        params={
            "session_token": authenticate(
                test_client,
                wg_credentials,
                ensure_db_api,
            ),
            "key": "non_existent_key"
        },
    )
    assert invalid_delete_response.status_code == 404


if __name__ == "__main__":
    pytest.main(["-v", __file__])
