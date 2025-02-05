import pytest
import os
import subprocess
import signal
import time
import requests
from pathlib import Path
from fastapi import HTTPException
from services.database_service import DatabaseService, DBConfig
from services.profile_service import ProfileService
from utils.browser_manager import BrowserManager
from clients.database_client import DatabaseClient
from clients.auth_client import AuthClient
from tests.logger import TestLogger

logger = TestLogger(Path(__file__).stem)


@pytest.fixture(scope="session")
def credentials() -> dict:
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
        response = requests.get(f"{api_url}/health")
        if response.status_code == 200 and response.json().get("status") == "healthy":
            yield api_url
            return
    except requests.RequestException:
        api_process = subprocess.Popen([
            "python",
            "-m",
            "api.v1.database",
        ], preexec_fn=os.setsid)

        for _ in range(10):
            try:
                response = requests.get(f"{api_url}/health")
                if response.status_code == 200 and response.json().get("status") == "healthy":
                    break
            except requests.RequestException:
                time.sleep(1)
        else:
            if api_process:
                os.killpg(os.getpgid(api_process.pid), signal.SIGTERM)
            pytest.fail("Database API failed to start")

    yield api_url

    if api_process:
        os.killpg(os.getpgid(api_process.pid), signal.SIGTERM)


@pytest.fixture(scope="session")
def ensure_auth_api(credentials):
    """Ensure auth API is running and healthy."""
    api_url = "http://localhost:8000"
    api_process = None

    try:
        response = requests.get(f"{api_url}/health")
        if response.status_code == 200 and response.json().get("status") == "healthy":
            # response = requests.post(
            #     f"{api_url}/authenticate/wg-gesucht",
            #     json=credentials,
            # )
            yield api_url
            return
    except requests.RequestException:
        api_process = subprocess.Popen([
            "python",
            "-m",
            "api.v1.auth",
        ], preexec_fn=os.setsid)

        for _ in range(10):
            try:
                response = requests.get(f"{api_url}/health")
                if response.status_code == 200 and response.json().get("status") == "healthy":
                    break
            except requests.RequestException:
                time.sleep(1)
        else:
            if api_process:
                os.killpg(os.getpgid(api_process.pid), signal.SIGTERM)
            pytest.fail("Auth API failed to start")

    # response = requests.post(
    #     f"{api_url}/authenticate/wg-gesucht",
    #     json=credentials,
    # )

    yield api_url

    if api_process:
        os.killpg(os.getpgid(api_process.pid), signal.SIGTERM)


@pytest.fixture(scope="session")
def db_client(ensure_db_api):
    """Create database client instance."""
    return DatabaseClient(ensure_db_api)


@pytest.fixture(scope="session")
def auth_client(ensure_auth_api):
    """Create database client instance."""
    return AuthClient(ensure_auth_api)


@pytest.fixture(scope="session")
def browser_manager():
    """Create browser manager instance."""
    return BrowserManager()


@pytest.fixture(scope="session")
def db_service(db_config):
    """Create database service instance."""
    return DatabaseService(db_config)


@pytest.fixture(scope="module")
def cleanup_database(db_service: DatabaseService):
    """Clean up test data from database before and after tests."""
    # Clean up before test
    db_service.execute_query(
        "DELETE FROM sessions WHERE user_id IN (SELECT id::text FROM users WHERE email = 'amadou.6e@googlemail.com')"
    )
    db_service.execute_query("DELETE FROM users WHERE email = 'amadou.6e@googlemail.com'")
    yield


@pytest.fixture(scope="module")
def cleanup_vault_files():
    """Clean up vault files before and after tests."""
    vault_dir = Path(os.getenv("WORKINGDIR", "."), "data", "users")
    if vault_dir.exists():
        os.system(f"rm -rf {vault_dir}")
    yield


@pytest.fixture(scope="function")
def profile_service(
    browser_manager: BrowserManager,
    ensure_db_api: str,
    ensure_auth_api: str,
) -> ProfileService:
    """Create profile service instance with all required dependencies."""
    return ProfileService(browser_manager=browser_manager)


@pytest.fixture(scope="module")
def authenticated_session(
    credentials: dict,
    ensure_db_api: str,
    auth_client: AuthClient,
    cleanup_database,
    cleanup_vault_files,
) -> str:
    """Get an authenticated session token for testing."""
    response = auth_client.authenticate_wg_gesucht(
        credentials["email"],
        credentials["password"],
    )
    return response["session_token"]


def test_get_profile_photo(
    profile_service: ProfileService,
    authenticated_session: str,
):
    """Test profile photo retrieval."""
    logger.info("Testing profile photo retrieval")
    photo_url = profile_service.get_profile_photo(authenticated_session)
    assert photo_url.startswith("https://")
    assert ".jpg" in photo_url.lower() or ".png" in photo_url.lower()
    logger.info(f"Successfully retrieved photo URL: {photo_url}")


def test_get_profile_name(
    profile_service: ProfileService,
    authenticated_session: str,
):
    """Test profile name retrieval."""
    logger.info("Testing profile name retrieval")
    name_info = profile_service.get_profile_name(authenticated_session)
    assert name_info["first_name"] and isinstance(name_info["first_name"], str)
    assert name_info["last_name"] and isinstance(name_info["last_name"], str)
    logger.info(f"Successfully retrieved name: {name_info}")


def test_get_user_address(
    profile_service: ProfileService,
    authenticated_session: str,
):
    """Test user address retrieval."""
    logger.info("Testing user address retrieval")
    address = profile_service.get_user_address(authenticated_session)
    assert address["city"] and isinstance(address["city"], str)
    assert address["postal_code"] and isinstance(address["postal_code"], str)
    assert address["street_and_house_number"] \
        and isinstance(address["street_and_house_number"], str)
    logger.info(f"Successfully retrieved address: {address}")


def test_download_profile_photo(
    profile_service: ProfileService,
    authenticated_session: str,
):
    """Test profile photo download."""
    logger.info("Testing profile photo download")
    save_path = profile_service.download_profile_photo(authenticated_session)
    assert Path(save_path).exists()
    assert Path(save_path).stat().st_size > 0
    logger.info(f"Successfully downloaded photo to: {save_path}")
    Path(save_path).unlink()


def test_caching_behavior(
    profile_service: ProfileService,
    authenticated_session: str,
    db_client: DatabaseClient,
):
    """Test that data is properly cached in the database."""
    logger.info("Testing caching behavior")

    # Get profile info which should cache it
    photo_url = profile_service.get_profile_photo(authenticated_session)
    name_info = profile_service.get_profile_name(authenticated_session)

    # Verify it's stored in database
    user_id = profile_service.auth_client.get_user_id(authenticated_session)
    result = db_client.select(
        table="users",
        conditions=f"id = '{user_id}'",
        fields=["profile_photo", "first_name", "last_name"],
    )

    assert result["data"]
    assert result["data"][0]["profile_photo"] == photo_url
    assert result["data"][0]["first_name"] == name_info["first_name"]
    assert result["data"][0]["last_name"] == name_info["last_name"]


if __name__ == "__main__":
    pytest.main(["-v", __file__])
