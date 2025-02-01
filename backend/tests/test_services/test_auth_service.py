import pytest
from pathlib import Path
from services.auth_service import AuthService
from services.database_service import DatabaseService, DBConfig
from utils.browser_manager import BrowserManager
from fastapi import HTTPException
from cryptography.fernet import Fernet
from typing import Dict
from datetime import datetime
import os

@pytest.fixture(scope="session")
def credentials() -> Dict[str, str]:
    """Fixture to provide database credentials."""
    return {
        "user": os.getenv("POSTGRES_ROLE"),
        "password": os.getenv("POSTGRES_PWD"),
    }

@pytest.fixture(scope="session")
def db_config(credentials: Dict[str, str]) -> DBConfig:
    """Fixture to create database configuration."""
    return DBConfig(
        host="localhost",
        port=5432,
        database="postgres",
        user=credentials["user"],
        password=credentials["password"],
    )

@pytest.fixture(scope="session")
def db_service(db_config: DBConfig) -> DatabaseService:
    """Fixture to create a long-lived database service instance."""
    return DatabaseService(db_config)

@pytest.fixture(scope="session")
def browser_manager() -> BrowserManager:
    """Fixture to create a browser manager."""
    return BrowserManager()

@pytest.fixture(scope="function")
def clean_key_vault():
    """Fixture to clean up the key vault directory using os.system."""
    key_vault_dir = Path(os.getenv("WORKINGDIR", "."), "data", "users")

    # Clean up before tests
    if key_vault_dir.exists():
        os.system(f"rm -rf {key_vault_dir}")

    yield

    # Clean up again after tests
    if key_vault_dir.exists():
        os.system(f"rm -rf {key_vault_dir}")

@pytest.fixture(scope="function")
def auth_service(db_service: DatabaseService, browser_manager: BrowserManager) -> AuthService:
    """Fixture to create an AuthService instance."""
    return AuthService(db_service=db_service, browser_manager=browser_manager)

@pytest.mark.asyncio
async def test_wg_gesucht_authentication(auth_service: AuthService, clean_key_vault, db_service: DatabaseService):
    """Test authenticating and storing WG-Gesucht credentials."""
    email = "test@example.com"
    password = "securepassword"

    # Insert test data for user
    db_service.insert("users", {"email": email, "wg_password": Fernet.generate_key(), "created_at": datetime.now()})

    # Authenticate
    credentials = {"email": email, "password": password}
    result = await auth_service.authenticate_wg_gesucht(credentials)
    assert result.message == "Successfully authenticated with WG-Gesucht"
    assert result.session_token is not None

    # Verify credentials stored in key vault
    user_id = str(result.user_id)
    wg_password = auth_service._load_from_vault(user_id, "wg_password")
    assert wg_password == password

def test_openai_key_storage(auth_service: AuthService, clean_key_vault, db_service: DatabaseService):
    """Test storing OpenAI API keys in the key vault."""
    user_id = "123"
    api_key = "sk-test-openai-key"

    # Store API key
    session_token = auth_service._generate_session_token(user_id)
    credentials = {"api_key": api_key}
    result = auth_service.authenticate_openai(session_token, credentials)
    assert result.message == "Successfully stored OpenAI API key"

    # Verify API key stored in key vault
    stored_key = auth_service._load_from_vault(user_id, "openai_key")
    assert stored_key == api_key

def test_retrieve_credentials(auth_service: AuthService, clean_key_vault, db_service: DatabaseService):
    """Test retrieving stored credentials from the key vault."""
    user_id = "123"
    wg_password = "securepassword"
    openai_key = "sk-test-openai-key"

    # Store credentials in the key vault
    auth_service._save_to_vault(user_id, "wg_password", wg_password)
    auth_service._save_to_vault(user_id, "openai_key", openai_key)

    # Retrieve credentials
    session_token = auth_service._generate_session_token(user_id)
    credentials = auth_service.get_credentials(session_token)
    assert credentials["wg_password"] == wg_password
    assert credentials["openai_key"] == openai_key

def test_invalid_login(auth_service: AuthService, clean_key_vault, browser_manager: BrowserManager):
    """Test handling of invalid WG-Gesucht credentials."""
    email = "invalid@example.com"
    password = "wrongpassword"

    # Simulate invalid login using browser manager
    browser_manager.get_browser_for_user(email).login = lambda x, y: False

    with pytest.raises(HTTPException) as exc_info:
        credentials = {"email": email, "password": password}
        auth_service.authenticate_wg_gesucht(credentials)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid WG-Gesucht credentials"

def test_invalid_openai_key(auth_service: AuthService, clean_key_vault):
    """Test handling of invalid OpenAI API keys."""
    user_id = "123"
    invalid_key = "sk-invalid-key"

    # Mock OpenAI API key validation failure
    with pytest.raises(HTTPException) as exc_info:
        session_token = auth_service._generate_session_token(user_id)
        credentials = {"api_key": invalid_key}
        auth_service.authenticate_openai(session_token, credentials)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid OpenAI API key"

# if __name__ == "__main__":
# pytest.main(["-v", __file__])
if __name__ == "__main__":
    # Set up database configuration
    db_config = DBConfig(
        host="localhost",
        port=5432,
        database="postgres",
        user=os.getenv("POSTGRES_ROLE", "test_user"),
        password=os.getenv("POSTGRES_PWD", "test_password"),
    )
    db_service = DatabaseService(db_config)

    # Set up browser manager
    browser_manager = BrowserManager()

    # Set up AuthService
    auth_service = AuthService(db_service, browser_manager)
    import shutil
    import asyncio
    # Clean key vault directory
    key_vault_dir = Path(os.getenv("WORKINGDIR", "."), "data", "users")
    if key_vault_dir.exists():
        shutil.rmtree(key_vault_dir)
    key_vault_dir.mkdir(parents=True, exist_ok=True)

    # Manually call the test function
    asyncio.run(test_wg_gesucht_authentication(auth_service=auth_service, clean_key_vault=None, db_service=db_service))