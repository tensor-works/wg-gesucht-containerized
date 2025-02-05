import pytest
from utils.browser_manager import BrowserManager
from tests.logger import TestLogger
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = TestLogger(Path(__file__).stem)


@pytest.fixture
def browser():
    logger.info("Setting up BrowserManager")
    browser_manager = BrowserManager()
    yield browser_manager.get_browser_for_user("test_user1")


@pytest.fixture
def credentials():
    return {"email": "amadou.6e@googlemail.com", "password": "SomePassworFrSkrr"}


@pytest.fixture(scope="session")
def browser_manager():
    logger.info("Setting up BrowserManager")
    manager = BrowserManager()
    yield manager
