import requests
from fastapi import HTTPException
from typing import Optional


class ProfileClient:

    def __init__(self, profile_api_url: str = "http://localhost:8001"):
        self.profile_api_url = profile_api_url.rstrip("/")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> dict:
        url = f"{self.profile_api_url}{endpoint}"
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            try:
                error_detail = e.response.json()
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=error_detail.get("detail", str(e)),
                )
            except ValueError:
                raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Profile API request failed: {str(e)}")

    def health_check(self) -> dict:
        """Check API health status."""
        return self._make_request("GET", "/health")

    def get_profile_photo(self, session_token: str) -> str:
        """Get user's profile photo URL."""
        response = self._make_request(
            "GET",
            "/profile/photo",
            params={"session_token": session_token},
        )
        return response["photo_url"]

    def get_profile_name(self, session_token: str) -> dict:
        """Get user's name details."""
        return self._make_request(
            "GET",
            "/profile/name",
            params={"session_token": session_token},
        )

    def get_profile_address(self, session_token: str) -> dict:
        """Get user's address details."""
        return self._make_request(
            "GET",
            "/profile/address",
            params={"session_token": session_token},
        )

    def download_profile_photo(
        self,
        session_token: str,
        save_path: Optional[str] = None,
    ) -> str:
        """Download user's profile photo."""
        response = self._make_request(
            "POST",
            "/profile/photo/download",
            params={
                "session_token": session_token,
                "save_path": save_path
            },
        )
        return response["photo_path"]
