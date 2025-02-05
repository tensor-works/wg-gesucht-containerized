import os
import requests
import imghdr
from utils import getenv
from pathlib import Path
from fastapi import HTTPException
from selenium.webdriver.common.by import By
from utils.browser_manager import BrowserManager
from utils.browser_wrapper import BrowserWrapper
from clients.database_client import DatabaseClient
from clients.auth_client import AuthClient


class ProfileService:

    def __init__(
        self,
        browser_manager: BrowserManager,
        auth_api_url: str = "http://localhost:8000",
        db_api_url: str = "http://localhost:7999",
    ):
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
        self.browser_manager = browser_manager
        self.auth_api_url = auth_api_url.rstrip("/")
        self.db_api_url = db_api_url.rstrip("/")
        self.db_client = DatabaseClient(db_api_url)
        self.auth_client = AuthClient(auth_api_url)

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
        user_dir = Path(getenv("WORKDIR", "."), "data", "users", user_id, "profile")
        user_dir.mkdir(parents=True, exist_ok=True)
        return user_dir

    def _login_browser(self, session_token: str, browser: BrowserWrapper):
        if browser.is_logged_in():
            return
        creds = self.auth_client.get_credentials(session_token)
        browser.login(creds["email"], creds["wg_password"])
        return

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

        user_id = self.auth_client.get_user_id(session_token)

        result = self.db_client.select(
            table="users",
            conditions=f"id = '{user_id}'",
            fields=["profile_photo"],
        )
        if result["success"] and result["data"][0].get("profile_photo"):
            return result["data"][0].get("profile_photo")

        # Fetch from WG-Gesucht if not stored
        browser = self.browser_manager.get_browser_for_user(user_id)
        self._login_browser(session_token, browser)
        browser.navigate_to("https://www.wg-gesucht.de/my-profile.html")

        try:
            img_element = browser.get_element(By.ID, "my_profile_profile_image")
            photo_url = img_element.get_attribute("src")
            if not photo_url:
                raise HTTPException(status_code=404, detail="Profile photo not found")
        except Exception:
            raise HTTPException(status_code=404, detail="Profile photo not found")

        # Store profile photo URL in database
        self.db_client.update(
            table="users",
            data={"profile_photo": photo_url},
            conditions=f"id = '{user_id}'",
        )

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
        user_id = self.auth_client.get_user_id(session_token)

        # Check if the name exists in the database
        result = self.db_client.select(
            table="users",
            conditions=f"id = '{user_id}'",
            fields=["first_name", "last_name"],
        )

        if result["success"] and result["data"]:
            first_name = result["data"][0].get("first_name")
            last_name = result["data"][0].get("last_name")
            if first_name and last_name:
                return {"first_name": first_name, "last_name": last_name}

        # Fetch from WG-Gesucht if not stored
        browser = self.browser_manager.get_browser_for_user(user_id)
        self._login_browser(session_token, browser)
        browser.navigate_to("https://www.wg-gesucht.de/my-profile.html")

        first_name = browser.get_element(By.ID, "first_name").get_attribute("value")
        last_name = browser.get_element(By.ID, "last_name").get_attribute("value")

        if not first_name or not last_name:
            raise HTTPException(status_code=404, detail="User name not found")

        # Store name in database
        self.db_client.update(
            table="users",
            data={
                "first_name": first_name,
                "last_name": last_name
            },
            conditions=f"id = '{user_id}'",
        )

        return {
            "first_name": first_name,
            "last_name": last_name,
        }

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
        user_id = self.auth_client.get_user_id(session_token)

        # Check if the address exists in the database
        result = self.db_client.select(
            table="users",
            conditions=f"id = '{user_id}'",
            fields=["city", "postal_code", "street_and_house_number"],
        )

        if result["success"] and result["data"]:
            city = result["data"][0].get("city")
            postal_code = result["data"][0].get("postal_code")
            street_address = result["data"][0].get("street_and_house_number")
            if city and postal_code and street_address:
                return {
                    "city": city,
                    "postal_code": postal_code,
                    "street_and_house_number": street_address
                }

        # Fetch from WG-Gesucht if not stored
        browser = self.browser_manager.get_browser_for_user(user_id)
        self._login_browser(session_token, browser)
        browser.navigate_to("https://www.wg-gesucht.de/my-profile.html")
        city = browser.get_element(By.ID, "city").get_attribute("value")
        postal_code = browser.get_element(By.ID, "postcode").get_attribute("value")
        street_address = browser.get_element(By.ID, "street").get_attribute("value")

        if not city or not postal_code or not street_address:
            raise HTTPException(status_code=404, detail="User address not found")

        # Store address in database
        self.db_client.update(
            table="users",
            data={
                "city": city,
                "postal_code": postal_code,
                "street_and_house_number": street_address
            },
            conditions=f"id = '{user_id}'",
        )
        return {
            "city": city,
            "postal_code": postal_code,
            "street_and_house_number": street_address,
        }

    def download_profile_photo(
        self,
        session_token: str,
        save_path: str = None,
    ) -> str:
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

        user_id = self.auth_client.get_user_id(session_token)
        photo_url = self.get_profile_photo(session_token)

        if not save_path:
            save_path = str(Path(self._get_user_dir(user_id), "profile_photo.jpg"))

        response = requests.get(photo_url)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)

            # Check if the file is a valid image
            if not imghdr.what(save_path):
                os.remove(save_path)
                raise HTTPException(status_code=500, detail="Invalid profile image")

            return save_path

        raise HTTPException(status_code=500, detail="Failed to download profile photo")
