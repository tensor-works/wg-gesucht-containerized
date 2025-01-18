import pytest
import logging
import os
from unittest.mock import Mock, patch, MagicMock
from selenium.common.exceptions import ElementNotInteractableException
from selenium.webdriver.common.by import By
from submit_wg import submit_app

# Mock logging setup
logger = logging.getLogger("test_logger")

@pytest.fixture
def mock_config():
    os.environ["PASSWORD"] = "test123"
    return {
        "run_headless": True,
        "chromedriver_path": "/fake/path/chromedriver",
        "ref": "/wg-zimmer-in-Berlin.123.html",
        "wg_gesucht_credentials": {
            "email": "test@example.com",
        },
        "user_name": "Test User",
        "address": "Test Address",
        "messages": {
            "english": "message_en.txt"
        }
    }

@pytest.fixture
def mock_webdriver():
    with patch('selenium.webdriver.Chrome') as mock_chrome:
        # Create a mock driver instance
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        
        # Mock find_elements to return empty list for cookie popup
        mock_driver.find_elements.return_value = []
        
        # Setup basic element mocks
        mock_element = MagicMock()
        mock_driver.find_element.return_value = mock_element
        
        yield mock_driver

@pytest.fixture
def mock_service():
    with patch('selenium.webdriver.chrome.service.Service') as mock_svc:
        yield mock_svc

@pytest.fixture
def mock_file():
    with patch('builtins.open', create=True) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = "Hello {recipient}!"
        yield mock_open

def test_successful_submission(mock_config, mock_webdriver, mock_service, mock_file):
    """Test a successful message submission scenario"""
    
    # Configure mock element to be found and interactable
    mock_webdriver.find_element.return_value = MagicMock(interactable=True)
    
    # Mock successful button clicks
    def mock_click(*args, **kwargs):
        return True
    mock_webdriver.find_element.return_value.click = mock_click
    
    result = submit_app(mock_config, logger)
    
    assert result is True
    # Verify login occurred
    mock_webdriver.find_element.assert_any_call(By.ID, "login_email_username")
    mock_webdriver.find_element.assert_any_call(By.ID, "login_password")
    mock_webdriver.find_element.assert_any_call(By.ID, "login_submit")

def test_failed_login(mock_config, mock_webdriver, mock_service):
    """Test scenario where login fails"""
    
    # Make login button click fail
    mock_webdriver.find_element.return_value.click.side_effect = ElementNotInteractableException()
    
    with pytest.raises(ElementNotInteractableException):
        submit_app(mock_config, logger)

def test_message_already_sent(mock_config, mock_webdriver, mock_service):
    """Test scenario where message was already sent"""
    
    # Mock successful login
    mock_webdriver.find_element.return_value.click = lambda: None
    
    # Make message_timestamp element findable (indicates message was sent)
    def mock_find_element(by, id):
        if id == "message_timestamp":
            return MagicMock()
        return MagicMock()
    mock_webdriver.find_element.side_effect = mock_find_element
    
    result = submit_app(mock_config, logger)
    assert result is False

def test_missing_message_file(mock_config, mock_webdriver, mock_service):
    """Test handling of missing message file"""
    
    # Mock successful login
    mock_webdriver.find_element.return_value.click = lambda: None
    
    # Make open() raise FileNotFoundError
    with patch('builtins.open', side_effect=FileNotFoundError):
        result = submit_app(mock_config, logger)
        assert result is False

def test_gpt_language_detection(mock_config, mock_webdriver, mock_service, mock_file):
    """Test GPT language detection integration"""
    
    # Add OpenAI key to config to trigger GPT usage
    mock_config["openai_credentials"]["api_key"] = "fake-key"
    mock_config["listing_text"] = "This is an English text"
    mock_config["messages"] = {"english": "en.txt", "german": "de.txt"}
    
    # Mock OpenAI response
    with patch('src.OpenAIHelper') as mock_openai:
        mock_openai.return_value.generate.return_value = '{"language": "English"}'
        
        result = submit_app(mock_config, logger)
        
        # Verify OpenAI was called
        mock_openai.assert_called_once()
        assert result is True

def test_driver_creation_failure(mock_config):
    """Test handling of Chrome driver creation failure"""
    
    # Mock Chrome driver to raise exception
    with patch('selenium.webdriver.Chrome', side_effect=Exception("Driver failed")):
        with pytest.raises(Exception) as exc_info:
            submit_app(mock_config, logger)
        assert "Driver failed" in str(exc_info.value)

# Additional test ideas:
# - Test cookie popup handling
# - Test security confirmation popup handling
# - Test message submission button not found
# - Test various GPT response formats
# - Test network timeout scenarios