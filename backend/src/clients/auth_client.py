import requests
from fastapi import HTTPException


class AuthClient:
    """
    A client for interacting with the Authentication API.

    Provides methods similar to AuthService but communicates over HTTP.
    """

    def __init__(self, auth_api_url: str = "http://localhost:8000"):
        """
        Initialize the AuthClient.

        Parameters
        ----------
        auth_api_url : str
            The base URL of the authentication API service.
        """
        self.auth_api_url = auth_api_url.rstrip("/")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> dict:
        """
        Generic method for making HTTP requests.

        Parameters
        ----------
        method : str
            HTTP method (GET, POST, DELETE).
        endpoint : str
            API endpoint (e.g., "/validate-token").
        **kwargs
            Additional request parameters (json, params, etc.).

        Returns
        -------
        dict
            The JSON response.

        Raises
        ------
        HTTPException
            If the request fails.
        """
        url = f"{self.auth_api_url}{endpoint}"
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            # Preserve the original FastAPI error status code and parse error message from API
            try:
                error_detail = e.response.json()
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=error_detail.get("detail", str(e)),
                )
            except ValueError:
                # If the response is not JSON, use the original error message
                raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except requests.RequestException as e:
            # For connection errors, timeouts, etc.
            raise HTTPException(status_code=500, detail=f"Auth API request failed: {str(e)}")

    def health_check(self) -> dict:
        """Check the health of the authentication service."""
        return self._make_request("GET", "/health")

    def authenticate_wg_gesucht(self, email: str, password: str) -> dict:
        """Authenticate with WG-Gesucht and return session token."""
        return self._make_request(
            "POST",
            "/authenticate/wg-gesucht",
            json={
                "email": email,
                "password": password
            },
        )

    def authenticate_openai(self, session_token: str, api_key: str) -> dict:
        """Authenticate and store OpenAI API key."""
        return self._make_request(
            "POST",
            "/authenticate/openai",
            params={"session_token": session_token},
            json={"api_key": api_key},
        )

    def validate_session_token(self, session_token: str) -> bool:
        """Validate a session token."""
        response = self._make_request(
            "GET",
            "/validate-token",
            params={"session_token": session_token},
        )
        return response.get("valid", False)

    def get_credentials(self, session_token: str) -> dict:
        """Retrieve stored user credentials."""
        return self._make_request(
            "GET",
            "/get-credentials",
            params={"session_token": session_token},
        )

    def delete_credentials(self, session_token: str, key: str) -> dict:
        """Delete a specific credential from the user's vault."""
        return self._make_request(
            "DELETE",
            "/delete-credentials",
            params={
                "session_token": session_token,
                "key": key
            },
        )

    def get_user_id(self, session_token: str) -> str:
        """
        Get the user ID associated with a session token.

        Parameters
        ----------
        session_token : str
            The JWT session token.

        Returns
        -------
        str
            The user ID associated with the token.

        Raises
        ------
        HTTPException
            If the token is invalid or the request fails.
        """
        response = self._make_request(
            "GET",
            "/get-user-id",
            params={"session_token": session_token},
        )
        return response["user_id"]
