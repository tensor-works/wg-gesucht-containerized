import os
import requests
from pathlib import Path
from fastapi import HTTPException
from selenium.webdriver.common.by import By
from utils.browser_wrapper import BrowserWrapper
from utils.browser_manager import BrowserManager
from services.auth_service import AuthService
from services.database_service import DatabaseService


class ProfileService:
    """
    Service for retrieving and managing user profile information from WG-Gesucht.

    Attributes
    ----------
    auth_service : AuthService
        Handles session validation and user ID retrieval.
    browser_manager : BrowserManager
        Manages browser sessions for WG-Gesucht interactions.
    db_service : DatabaseService
        Handles database interactions for storing profile data.
    """

    def __init__(self, auth_service: AuthService, browser_manager: BrowserManager,
                 db_service: DatabaseService):
        """
        Initializes the ProfileService.

        Parameters
        ----------
        auth_service : AuthService
            Instance of the authentication service.
        browser_manager : BrowserManager
            Instance of the browser manager.
        db_service : DatabaseService
            Instance of the database service.
        """
        self.auth_service = auth_service
        self.browser_manager = browser_manager
        self.db_service = db_service

    def _get_user_dir(self, user_id: str) -> Path:
        """
        Get the user's profile directory.

        Parameters
        ----------
        user_id : str
            The unique identifier of the user.

        Returns
        -------
        Path
            Path to the user's profile directory.
        """
        user_dir = Path(os.getenv("WORKDIR", "."), "data", "users", user_id, "profile")
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    def get_profile_photo(self, session_token: str) -> str:
        """
        Retrieve the user's profile photo.

        Parameters
        ----------
        session_token : str
            JWT session token for authentication.

        Returns
        -------
        str
            URL to the profile photo.

        Raises
        ------
        HTTPException
            If authentication fails or the profile photo is not found.
        """
        user_id = self.auth_service.get_user_id(session_token)

        # Check if the photo exists in the database
        result = self.db_service.select("users",
                                        conditions=f"id = '{user_id}'",
                                        fields=["profile_photo"])
        if result["success"] and result["data"] and result["data"][0]["profile_photo"]:
            return result["data"][0]["profile_photo"]

        # Fetch from WG-Gesucht if not stored
        browser = self.browser_manager.get_browser_for_user(user_id)
        browser.navigate_to("https://www.wg-gesucht.de/my-profile.html")
        img_element = browser.get_element(By.ID, "my_profile_profile_image")
        photo_url = img_element.get_attribute("src")

        if not photo_url:
            raise HTTPException(status_code=404, detail="Profile photo not found")

        # Store profile photo URL in database
        self.db_service.update("users", {"profile_photo": photo_url}, f"id = '{user_id}'")

        return photo_url

    def get_profile_name(self, session_token: str) -> dict:
        """
        Retrieve the user's first and last name.

        Parameters
        ----------
        session_token : str
            JWT session token for authentication.

        Returns
        -------
        dict
            Dictionary containing `first_name` and `last_name`.

        Raises
        ------
        HTTPException
            If authentication fails or the profile name is not found.
        """
        user_id = self.auth_service.get_user_id(session_token)

        # Check if the name exists in the database
        result = self.db_service.select("users",
                                        conditions=f"id = '{user_id}'",
                                        fields=["first_name", "last_name"])
        if result["success"] and result["data"] and result["data"][0]["first_name"]:
            return {
                "first_name": result["data"][0]["first_name"],
                "last_name": result["data"][0]["last_name"]
            }

        # Fetch from WG-Gesucht if not stored
        browser = self.browser_manager.get_browser_for_user(user_id)
        browser.navigate_to("https://www.wg-gesucht.de/my-profile.html")
        first_name = browser.get_element(By.ID, "first_name").get_attribute("value")
        last_name = browser.get_element(By.ID, "last_name").get_attribute("value")

        if not first_name or not last_name:
            raise HTTPException(status_code=404, detail="User name not found")

        # Store name in database
        self.db_service.update("users", {
            "first_name": first_name,
            "last_name": last_name
        }, f"id = '{user_id}'")

        return {"first_name": first_name, "last_name": last_name}

    def get_user_address(self, session_token: str) -> dict:
        """
        Retrieve the user's address details.

        Parameters
        ----------
        session_token : str
            JWT session token for authentication.

        Returns
        -------
        dict
            Dictionary containing `city`, `postal_code`, and `street_and_house_number`.

        Raises
        ------
        HTTPException
            If authentication fails or the address is not found.
        """
        user_id = self.auth_service.get_user_id(session_token)

        # Check if the address exists in the database
        result = self.db_service.select("users",
                                        conditions=f"id = '{user_id}'",
                                        fields=["city", "postal_code", "street_address"])
        if result["success"] and result["data"] and result["data"][0]["city"]:
            return {
                "city": result["data"][0]["city"],
                "postal_code": result["data"][0]["postal_code"],
                "street_and_house_number": result["data"][0]["street_address"],
            }

        # Fetch from WG-Gesucht if not stored
        browser = self.browser_manager.get_browser_for_user(user_id)
        browser.navigate_to("https://www.wg-gesucht.de/my-profile.html")
        city = browser.get_element(By.ID, "city").get_attribute("value")
        postal_code = browser.get_element(By.ID, "postal_code").get_attribute("value")
        street_address = browser.get_element(By.ID, "street").get_attribute("value")

        if not city or not postal_code or not street_address:
            raise HTTPException(status_code=404, detail="User address not found")

        # Store address in database
        self.db_service.update("users", {
            "city": city,
            "postal_code": postal_code,
            "street_address": street_address
        }, f"id = '{user_id}'")

        return {"city": city, "postal_code": postal_code, "street_and_house_number": street_address}

    def download_profile_photo(self, session_token: str, save_path: str = None) -> str:
        """
        Download the user's profile photo and save it locally.

        Parameters
        ----------
        session_token : str
            JWT session token for authentication.
        save_path : str, optional
            Path to save the downloaded profile photo. If not provided, it will be saved in the user's profile directory.

        Returns
        -------
        str
            Path where the profile photo was saved.

        Raises
        ------
        HTTPException
            If the profile photo is not found or the download fails.
        """
        user_id = self.auth_service.get_user_id(session_token)
        photo_url = self.get_profile_photo(session_token)

        if not save_path:
            save_path = str(self._get_user_dir(user_id) / "profile_photo.jpg")

        response = requests.get(photo_url)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return save_path

        raise HTTPException(status_code=500, detail="Failed to download profile photo")
