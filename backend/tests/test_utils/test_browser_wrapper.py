import pytest
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotInteractableException
from utils.browser_wrapper import BrowserWrapper
from utils.browser_manager import BrowserManager
from tests.logger import TestLogger 
from pathlib import Path
import os

logger = TestLogger(Path(__file__).stem)


def test_navigation(browser: BrowserWrapper):
    browser.navigate_to("https://www.wg-gesucht.de")
    assert "WG-Gesucht.de" in browser.get_title()

def test_get_element(browser: BrowserWrapper):
    browser.navigate_to("https://www.wg-gesucht.de")
    main_column = browser.get_element(By.ID, "main_column")
    assert main_column.is_displayed()

def test_login_flow(browser: BrowserWrapper, credentials):
    email = credentials["email"]
    password = credentials["password"]

    browser.login(email, password)
   
    # Try to hover over Mein Konto and see if Mein Profil appears
    browser.hover_and_click(
        (By.XPATH, "//a[contains(text(), 'Mein Konto')]"),
        (By.XPATH, "//a[contains(@href, '/my-profile.html')]")
    )
    browser.remove_cookies_popup()
    browser.driver.save_screenshot("after_hover_and_click.png")
    assert "my-profile" in browser.driver.current_url

def test_send_keys(browser: BrowserWrapper):
    browser.navigate_to("https://www.wg-gesucht.de")
    search_box = browser.get_element(By.ID, "autocompinp")
    test_text = "Berlin"
    browser.send_keys(By.ID, "autocompinp", test_text)
    assert search_box.get_attribute("value") == test_text

def test_click_button(browser: BrowserWrapper):
    browser.navigate_to("https://www.wg-gesucht.de")
    # Test clicking the login button (should be visible without login)
    browser.click_button(By.XPATH, "//*[contains(text(), 'Mein Konto')]")
    login_form = browser.get_element(By.ID, "login_email_username")
    assert login_form.is_displayed()

def test_error_handling(browser: BrowserWrapper):
    with pytest.raises(selenium.common.exceptions.TimeoutException):
        browser.get_element(By.ID, "nonexistent-element", timeout=1)
        
    with pytest.raises(selenium.common.exceptions.TimeoutException):
        browser.send_keys(By.ID, "nonexistent-element", "test")

def test_cookie_popup_removal(browser: BrowserWrapper):
    browser.navigate_to("https://www.wg-gesucht.de")
    # Initial check for cookie popup
    cookie_popup = browser.driver.find_elements(By.XPATH, "//div[@id='cmpbox' or @id='cmpbox2']")
    if cookie_popup:
        initial_count = len(cookie_popup)
        browser.remove_cookies_popup()
        remaining_popup = browser.driver.find_elements(By.XPATH, "//div[@id='cmpbox' or @id='cmpbox2']")
        assert len(remaining_popup) < initial_count

def test_page_source(browser: BrowserWrapper):
    browser.navigate_to("https://www.wg-gesucht.de")
    source = browser.get_page_source()
    assert isinstance(source, str)
    assert len(source) > 0
    assert "html" in source.lower()

if __name__ == "__main__":
    browser_manager = BrowserManager()
    pytest.main(["-v", __file__])
    # test_login_flow(browser_manager.get_browser_for_user("test_user1"))
