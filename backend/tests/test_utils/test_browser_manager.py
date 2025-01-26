import pytest
from selenium.webdriver.common.by import By
from utils.browser_manager import BrowserManager
from tests.logger import TestLogger
from pathlib import Path
import time

logger = TestLogger(Path(__file__).stem)

@pytest.fixture
def browser_manager(request):
    logger.info("Setting up BrowserManager")
    browser_manager = BrowserManager()
    yield browser_manager
    logger.info("Cleaning up BrowserManager")
    for user_id in list(browser_manager.active_browsers.keys()):
        logger.debug(f"Closing browser for user: {user_id}")
        browser_manager.close_user_browser(user_id)

def test_browser_creation(browser_manager: BrowserManager):
    logger.info("Testing browser creation")
    browser = browser_manager.get_browser_for_user("test_user1")
    logger.debug("Browser created")
    
    browser.navigate_to("https://www.wg-gesucht.de")
    logger.debug(f"Page title: {browser.get_title()}")
    
    assert "WG-Gesucht.de" in browser.get_title()
    assert "test_user1" in browser_manager.active_browsers
    logger.info("Browser creation test passed")

def test_browser_reuse(browser_manager: BrowserManager):
    logger.info("Testing browser reuse")
    
    browser1 = browser_manager.get_browser_for_user("test_user2")
    logger.debug("First browser instance created")
    
    browser2 = browser_manager.get_browser_for_user("test_user2")
    logger.debug("Second browser instance requested")
    
    assert browser1 == browser2
    assert len(browser_manager.active_browsers) == 1
    logger.info("Browser reuse test passed")

def test_multiple_users(browser_manager: BrowserManager):
    logger.info("Testing multiple user browsers")
    
    browser1 = browser_manager.get_browser_for_user("test_user3")
    browser2 = browser_manager.get_browser_for_user("test_user4")
    
    assert browser1 != browser2
    assert len(browser_manager.active_browsers) == 2
    logger.debug(f"Active browsers count: {len(browser_manager.active_browsers)}")
    logger.info("Multiple users test passed")

def test_cleanup_inactive(browser_manager: BrowserManager):
    logger.info("Testing inactive browser cleanup")
    
    browser = browser_manager.get_browser_for_user("test_user5")
    assert "test_user5" in browser_manager.active_browsers
    
    time.sleep(2)
    logger.debug("Running cleanup with 1 second timeout")
    browser_manager.cleanup_inactive_browsers(max_idle_time=1)
    
    assert "test_user5" not in browser_manager.active_browsers
    logger.info("Cleanup test passed")

def test_close_user_browser(browser_manager: BrowserManager):
    logger.info("Testing browser closure")
    
    browser_manager.get_browser_for_user("test_user6")
    assert "test_user6" in browser_manager.active_browsers
    
    browser_manager.close_user_browser("test_user6")
    assert "test_user6" not in browser_manager.active_browsers
    logger.info("Browser closure test passed")

def test_browser_health(browser_manager: BrowserManager):
    logger.info("Testing browser functionality")
    
    browser = browser_manager.get_browser_for_user("test_user7")
    browser.navigate_to("https://www.wg-gesucht.de")
    
    try:
        main_column = browser.get_element(By.ID, "main_column")
        assert main_column.is_displayed()
        logger.debug("Main column element found and visible")
    except Exception as e:
        logger.error(f"Failed to find main column: {str(e)}")
        raise
    
    logger.info("Browser health test passed")

if __name__ == "__main__":
    pytest.main(["-v", __file__])