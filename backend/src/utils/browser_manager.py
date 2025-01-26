from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import threading
import time
from utils.browser_wrapper import BrowserWrapper

class BrowserManager:
    def __init__(self):
        self.active_browsers = {}  # user_id -> (browser_wrapper, last_active_time)
        self.lock = threading.Lock()

    def get_browser_for_user(self, user_id: str, run_headless: bool = True):
        with self.lock:
            if user_id in self.active_browsers:
                browser_wrapper, last_active = self.active_browsers[user_id]
                self.active_browsers[user_id] = (browser_wrapper, time.time())
                return browser_wrapper

            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox") # <- this bad boi is needed when running in container
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")  # Optional for environments with no GPU
            chrome_options.add_argument("--window-size=1920x1080")  # Ensures proper rendering
            
            if run_headless:
                chrome_options.headless = True
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_argument("--reuse-tab")
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            driver = webdriver.Chrome(
                service=Service(executable_path="/usr/local/bin/chromedriver"),
                options=chrome_options
            )
            
            browser_wrapper = BrowserWrapper(driver)
            self.active_browsers[user_id] = (browser_wrapper, time.time())
            return browser_wrapper

    def cleanup_inactive_browsers(self, max_idle_time=3600):
        with self.lock:
            current_time = time.time()
            to_remove = []
            
            for user_id, (browser_wrapper, last_active) in self.active_browsers.items():
                if current_time - last_active > max_idle_time:
                    browser_wrapper.quit()
                    to_remove.append(user_id)
                    
            for user_id in to_remove:
                del self.active_browsers[user_id]

    def close_user_browser(self, user_id: str):
        with self.lock:
            if user_id in self.active_browsers:
                browser_wrapper, _ = self.active_browsers[user_id]
                browser_wrapper.quit()
                del self.active_browsers[user_id]