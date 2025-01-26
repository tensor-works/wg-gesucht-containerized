import os
import requests
from pathlib import Path
from cryptography.fernet import Fernet
from selenium.webdriver.common.by import By
from utils.browser_wrapper import BrowserWrapper
from utils.browser_manager import BrowserManager

class ProfileService:
    def __init__(self):
        self.app_dir = Path(os.getenv("WORKDIR"), "/app")
        self.credentials_dir = Path(self.app_dir, "pwd")
        self.user_dir = Path(self.app_dir, "user")
        self.credentials_file = self.credentials_dir / "credentials.enc"
        self.key_file = self.credentials_dir / "key.enc"
        self.credentials_dir.mkdir(parents=True, exist_ok=True)
        self.user_dir.mkdir(parents=True, exist_ok=True)
        
        if self.key_file.exists():
            with open(self.key_file, "rb") as f:
                self.key = f.read() 
        else:
            self.key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(self.key)
        self.cipher = Fernet(self.key)

    def get_profile_photo(self, browser: BrowserWrapper) -> str:
        browser.navigate_to("https://www.wg-gesucht.de/my-profile.html")
        img_element = browser.get_element(By.ID, "my_profile_profile_image")
        return img_element.get_attribute("src")

    def get_profile_name(self, browser: BrowserWrapper) -> tuple[str, str]:
        browser.navigate_to("https://www.wg-gesucht.de/my-profile.html") 
        first_name = browser.get_element(By.ID, "first_name").get_attribute("value")
        last_name = browser.get_element(By.ID, "last_name").get_attribute("value")
        return first_name, last_name

    def download_profile_photo(self, browser: BrowserWrapper, save_path: str = None) -> str:        
        photo_url = self.get_profile_photo(browser)
        if not photo_url:
            return None
        
        if not save_path:
            save_path = str(self.user_dir / "profile_photo.jpg")
            
        response = requests.get(photo_url)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return save_path
        return None
