from fastapi import Depends
from uitls.browser_manager import BrowserManager

browser_manager = BrowserManager()

async def get_browser(user_id: str):
    # Gets or creates a browser session for this user
    return browser_manager.get_browser_for_user(user_id)
