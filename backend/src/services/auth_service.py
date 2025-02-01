"""
AuthService Module
==================

This module provides authentication and credential management services for users
interacting with WG-Gesucht and OpenAI. It includes secure storage, session management,
and encryption functionalities.

Classes
-------
- `WGGesuchtCredentials`: Pydantic model for WG-Gesucht authentication credentials.
- `OpenAICredentials`: Pydantic model for OpenAI API credentials.
- `AuthResponse`: Pydantic model for authentication responses.
- `AuthService`: Main authentication service handling WG-Gesucht and OpenAI authentication.

Usage Example
-------------
```python
from database_service import DatabaseService, DBConfig
from utils.browser_manager import BrowserManager
from auth_service import AuthService

db_config = DBConfig(
    host="localhost",
    port=5432,
    database="mydb",
    user="admin",
    password="password"
)
db_service = DatabaseService(db_config)
browser_manager = BrowserManager()
auth_service = AuthService(db_service, browser_manager)
```
"""
from fastapi import HTTPException
from pydantic import BaseModel, EmailStr
from cryptography.fernet import Fernet
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
import secrets
import os
import openai
from pathlib import Path
from services.database_service import DatabaseService, DBConfig
from utils.browser_manager import BrowserManager


# Pydantic models for request/response validation
class WGGesuchtCredentials(BaseModel):
    """
    Pydantic model for WG-Gesucht authentication credentials.
    """
    email: EmailStr
    password: str


class OpenAICredentials(BaseModel):
    """
    Pydantic model for OpenAI API credentials.
    """
    api_key: str


class AuthResponse(BaseModel):
    """
    Pydantic model for authentication responses.
    """
    message: str
    user_id: Optional[str] = None
    session_token: Optional[str] = None


class AuthService:

    def __init__(
        self,
        db_service: DatabaseService,
        browser_manager: BrowserManager,
        session_duration: int = 7,
    ):
        """
        Authentication service for WG-Gesucht and OpenAI.

        This service handles user authentication, session management, encryption, 
        and secure credential storage.

        Parameters
        ----------
        db_service : DatabaseService
            Instance of the database service.
        browser_manager : BrowserManager
            Instance of the browser manager for WG-Gesucht interactions.
        session_duration : int, optional, default=7
            Duration of user session in days.
        """
        self._db_service = db_service
        self._browser_manager = browser_manager

        # Initialize encryption key for sensitive data
        self._encryption_key = os.getenv('ENCRYPTION_KEY', Fernet.generate_key())
        self._cipher = Fernet(self._encryption_key)

        # JWT settings
        self._jwt_secret = os.getenv('JWT_SECRET', secrets.token_urlsafe(32))
        self._jwt_algorithm = 'HS256'
        self._session_duration = timedelta(days=session_duration)

    def _encrypt_data(self, data: str) -> str:
        """
        Encrypt sensitive information before storing.

        Parameters
        ----------
        data : str
            The plaintext data to encrypt.

        Returns
        -------
        str
            Encrypted data as a string.
        """
        return self._cipher.encrypt(data.encode()).decode()

    def _decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive information.

        Parameters
        ----------
        encrypted_data : str
            The encrypted data string.

        Returns
        -------
        str
            Decrypted plaintext data.
        """
        return self._cipher.decrypt(encrypted_data.encode()).decode()

    def _generate_session_token(self, user_id: str) -> str:
        """
        Generate a JWT session token.

        Parameters
        ----------
        user_id : str
            Unique identifier for the user.

        Returns
        -------
        str
            JWT session token.
        """
        payload = {'user_id': user_id, 'exp': datetime.utcnow() + self._session_duration}
        return jwt.encode(payload, self._jwt_secret, algorithm=self._jwt_algorithm)

    def _initialize_vault(self, vault_path: Path) -> Fernet:
        """
        Validate a session token.

        Parameters
        ----------
        session_token : str
            JWT session token.

        Returns
        -------
        bool
            True if the token is valid, False otherwise.
        """
        if not vault_path.exists():
            # Generate and save a new encryption key if the vault does not exist
            key = Fernet.generate_key()
            vault_path.write_bytes(key)
        else:
            # Read the existing key from the vault file
            key = vault_path.read_bytes()
        return Fernet(key)

    def _save_to_vault(self, user_id: str, key: str, value: str):

        vault_path = self._get_vault_path(user_id)
        cipher = self._initialize_vault(vault_path)

        # Save encrypted data
        data = {key: value}
        encrypted_data = cipher.encrypt(str(data).encode())
        vault_path.write_bytes(encrypted_data)

    def _load_from_vault(self, user_id: str, key: str) -> Optional[str]:
        """Load a key-value pair from the user's key vault."""
        vault_path = self._get_vault_path(user_id)
        cipher = self._initialize_vault(vault_path)

        if not vault_path.exists():
            return None

        encrypted_data = vault_path.read_bytes()
        decrypted_data = cipher.decrypt(encrypted_data).decode()

        # Parse stored data
        data = eval(decrypted_data)  # Ensure no untrusted input is present
        return data.get(key)

    def _get_vault_path(self, user_id: str) -> Path:
        """Get the path to the user's key vault."""
        user_dir = Path(os.getenv("WORKINGDIR", "."), "data", "users", user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        return Path(user_dir, "key_vault.enc")

    def validate_session_token(self, session_token: str) -> bool:
        """
        Validate a session token.

        Parameters
        ----------
        session_token : str
            JWT session token.

        Returns
        -------
        bool
            True if the token is valid, False otherwise.
        """
        try:
            jwt.decode(session_token, self._jwt_secret, algorithms=[self._jwt_algorithm])
            return True
        except jwt.InvalidTokenError:
            return False

    def get_user_id(self, session_token: str) -> str:
        """
        Extract user_id from session token.

        Parameters
        ----------
        session_token : str
            JWT session token.

        Returns
        -------
        str
            Extracted user ID.

        Raises
        ------
        HTTPException
            If the token is invalid.
        """
        try:
            payload = jwt.decode(session_token, self._jwt_secret, algorithms=[self._jwt_algorithm])
            return payload['user_id']
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid session token")

    async def authenticate_wg_gesucht(self, credentials: Dict[str, str]) -> AuthResponse:
        """
        Authenticate user with WG-Gesucht credentials.

        Parameters
        ----------
        credentials : Dict[str, str]
            A dictionary containing 'email' and 'password'.

        Returns
        -------
        AuthResponse
            Authentication response with user ID and session token.

        Raises
        ------
        HTTPException
            If authentication fails.
        """
        try:
            # Extract email and password from credentials dictionary
            email = credentials.get("email")
            password = credentials.get("password")

            if not email or not password:
                raise HTTPException(status_code=400, detail="Missing email or password")

            # Try logging in with provided credentials
            browser = self._browser_manager.get_browser_for_user(email)
            login_success = browser.login(
                email,
                password,
            )
            if not login_success:
                raise HTTPException(status_code=401, detail="Invalid WG-Gesucht credentials")

            # Check if user exists in the database
            result = self._db_service.select(
                "users",
                conditions=f"email = '{email}'",
            )

            if not result["success"]:
                raise HTTPException(status_code=500, detail="Database error")

            if not result["data"]:
                # Create new user if it doesn't exist
                user_id = str(datetime.now().timestamp()).replace(
                    ".", "")  # Generate a temporary user_id
                user_data = {"email": email, "created_at": datetime.now()}
                insert_result = self._db_service.insert("users", user_data)
                if not insert_result["success"]:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to create user: {insert_result['error']}",
                    )

                # Retrieve the newly created user
                result = self._db_service.select(
                    "users",
                    conditions=f"email = '{email}'",
                )
            else:
                # User exists, use their ID
                user_id = str(result["data"][0]["id"])

            # Save WG-Gesucht password to the key vault
            self._save_to_vault(
                user_id,
                "wg_password",
                password,
            )

            # Generate a session token
            session_token = self._generate_session_token(user_id)

            # Store the session token in the database
            session_data = {
                "user_id": user_id,
                "token": session_token,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + self._session_duration
            }
            session_result = self._db_service.insert("sessions", session_data)
            if not session_result["success"]:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create session: {session_result['error']}",
                )

            return AuthResponse(
                message="Successfully authenticated with WG-Gesucht",
                user_id=user_id,
                session_token=session_token,
            )

        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            if 'browser' in locals():
                browser.quit()

    async def authenticate_openai(self, session_token: str,
                                  credentials: OpenAICredentials) -> AuthResponse:
        """
        Retrieve user's stored credentials.

        Parameters
        ----------
        session_token : str
            JWT session token.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing user credentials.

        Raises
        ------
        HTTPException
            If user is not found or retrieval fails.
        """
        try:
            user_id = self.get_user_id(session_token)

            # Validate the API key with OpenAI
            openai.api_key = credentials.api_key
            try:
                openai.Model.list()
            except Exception:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid OpenAI API key",
                )

            # Save the API key securely to the user's key vault
            self._save_to_vault(
                user_id,
                "openai_key",
                credentials.api_key,
            )

            # Optionally store metadata in the database if needed
            update_result = self._db_service.update(
                "users",
                {"openai_key": "Stored in key vault"},
                f"id = '{user_id}'",
            )

            if not update_result["success"]:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to update OpenAI key metadata in database",
                )

            return AuthResponse(message="Successfully stored OpenAI API key")

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_credentials(self, session_token: str) -> Dict[str, Any]:
        """Retrieve user's credentials."""
        try:
            # Extract user_id from the session token
            user_id = self.get_user_id(session_token)

            # Query the database for user information
            result = self._db_service.select("users", conditions=f"id = '{user_id}'")

            if not result["success"] or not result["data"]:
                raise HTTPException(status_code=404, detail="User not found")

            user_data = result["data"][0]
            credentials = {"email": user_data["email"]}

            # Retrieve WG-Gesucht password from the key vault
            wg_password = self._load_from_vault(user_id, "wg_password")
            if wg_password:
                credentials["wg_password"] = wg_password
            else:
                # Fallback to decrypting from database if not in the vault
                credentials["wg_password"] = self._decrypt_data(user_data["wg_password"])

            # Retrieve OpenAI API key from the key vault
            openai_key = self._load_from_vault(user_id, "openai_key")
            if openai_key:
                credentials["openai_key"] = openai_key
            elif user_data.get("openai_key"):
                # Fallback to decrypting from database if not in the vault
                credentials["openai_key"] = self._decrypt_data(user_data["openai_key"])

            return credentials

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
