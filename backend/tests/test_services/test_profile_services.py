import pytest
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from utils.browser_manager import BrowserManager
from services.profile_service import ProfileService
from tests.logger import TestLogger
from utils.browser_wrapper import BrowserWrapper

logger = TestLogger(Path(__file__).stem)

@pytest.fixture(scope="session")
def credentials():
    return {
        "email": "amadou.6e@googlemail.com",
        "password": "SomePassworFrSkrr"
    }

@pytest.fixture(scope="session")
def browser_manager():
    manager = BrowserManager()
    yield manager

@pytest.fixture(scope="function")
def clean_pwd_dir():
    pwd_dir = Path("/app/pwd")
    if pwd_dir.exists():
        for file in pwd_dir.glob("*"):
            file.unlink()
        pwd_dir.rmdir()
    yield
    if pwd_dir.exists():
        for file in pwd_dir.glob("*"):
            file.unlink()
        pwd_dir.rmdir()

@pytest.fixture(scope="function")
def profile_service(clean_pwd_dir):
    service = ProfileService()
    yield service

@pytest.fixture
def logged_in_browser(browser_manager, credentials):
    browser = browser_manager.get_browser_for_user(credentials["email"])
    browser.login(credentials["email"], credentials["password"])
    yield browser
    browser.quit()

def test_service_initialization(profile_service: ProfileService):
    logger.info("Testing service initialization")
    assert profile_service.credentials_dir.exists()
    assert profile_service.credentials_dir.is_dir()
    assert profile_service.key_file.exists()
    with open(profile_service.key_file, "rb") as f:
        key_data = f.read()
    assert len(key_data) == 44

def test_get_profile_photo(profile_service: ProfileService, logged_in_browser: BrowserWrapper):
    logger.info("Testing profile photo retrieval")
    try:
        photo_url = profile_service.get_profile_photo(logged_in_browser)
        assert photo_url.startswith("https://")
        assert ".jpg" in photo_url.lower() or ".png" in photo_url.lower()
        logger.info(f"Successfully retrieved photo URL: {photo_url}")
    except TimeoutException as e:
        pytest.fail(f"Failed to get profile photo: {str(e)}")

def test_download_profile_photo(profile_service: ProfileService, logged_in_browser: BrowserWrapper):
    logger.info("Testing profile photo download")
    try:
        save_path = profile_service.download_profile_photo(logged_in_browser)
        assert save_path and Path(save_path).exists()
        assert Path(save_path).stat().st_size > 0
        logger.info(f"Successfully downloaded photo to: {save_path}")
        Path(save_path).unlink()
    except Exception as e:
        pytest.fail(f"Failed to download profile photo: {str(e)}")

def test_get_profile_name(profile_service: ProfileService, logged_in_browser: BrowserWrapper):
    logger.info("Testing profile name retrieval")
    try:
        first_name, last_name = profile_service.get_profile_name(logged_in_browser)
        assert first_name and isinstance(first_name, str)
        assert last_name and isinstance(last_name, str)
        assert len(first_name) > 0 and len(last_name) > 0
        logger.info(f"Successfully retrieved name: {first_name} {last_name}")
    except TimeoutException as e:
        pytest.fail(f"Failed to get profile name: {str(e)}")

def test_credential_encryption(profile_service: ProfileService, credentials):
    """Test encryption/decryption functionality"""
    logger.info("Testing credential encryption") 
    test_data = f"{credentials['email']}:{credentials['password']}"
    encrypted = profile_service.cipher.encrypt(test_data.encode())
    
    # Verify encryption
    assert credentials["email"].encode() not in encrypted
    assert credentials["password"].encode() not in encrypted
    
    # Verify decryption 
    decrypted = profile_service.cipher.decrypt(encrypted).decode()
    assert decrypted == test_data

if __name__ == "__main__":
    pytest.main(["-v", __file__])