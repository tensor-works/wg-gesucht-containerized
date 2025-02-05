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
from openai import OpenAI
import jwt
import secrets
import os
import requests
import json
from clients.database_client import DatabaseClient
from pathlib import Path
from utils import getenv
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


class UserVault:
    """Handles secure storage and retrieval of user secrets."""

    def __init__(self, user_id: str, base_dir: Optional[str] = None):
        """
        Initialize the user's vault system.
        
        Parameters
        ----------
        user_id : str
            The unique identifier for the user
        base_dir : str, optional
            Base directory for storing vault files
        """
        self.user_id = user_id
        self.base_dir = Path(base_dir or getenv("WORKDIR"))
        self.user_dir = Path(self.base_dir, "data", "users", user_id, "vault")
        self.user_dir.mkdir(parents=True, exist_ok=True)

        # Initialize or load the master key
        self._master_key = self._initialize_master_key()
        self._cipher = Fernet(self._master_key)

    def _initialize_master_key(self) -> bytes:
        """Initialize or load the master encryption key."""
        key_path = Path(self.user_dir, "master.key")

        if not key_path.exists():
            key = Fernet.generate_key()
            key_path.write_bytes(key)
            return key

        return key_path.read_bytes()

    def _get_secret_path(self, secret_type: str) -> Path:
        """Get path for a specific type of secret."""
        return Path(self.user_dir, f"{secret_type}.enc")

    def store_secret(self, secret_type: str, secret_data: Any) -> None:
        """
        Store an encrypted secret.
        
        Parameters
        ----------
        secret_type : str
            Type of secret (e.g., 'wg_password', 'openai_key')
        secret_data : Any
            Data to encrypt and store
        """
        # Convert data to string if it's not already
        if not isinstance(secret_data, str):
            secret_data = json.dumps(secret_data)

        # Encrypt and save
        encrypted_data = self._cipher.encrypt(secret_data.encode())
        secret_path = self._get_secret_path(secret_type)
        secret_path.write_bytes(encrypted_data)

    def get_secret(self, secret_type: str) -> Optional[str]:
        """
        Retrieve and decrypt a secret.
        
        Parameters
        ----------
        secret_type : str
            Type of secret to retrieve
            
        Returns
        -------
        Optional[str]
            Decrypted secret if found, None otherwise
        """
        secret_path = self._get_secret_path(secret_type)

        if not secret_path.exists():
            return None

        try:
            encrypted_data = secret_path.read_bytes()
            decrypted_data = self._cipher.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception:
            return None

    def list_secrets(self) -> list[str]:
        """List all available secret types."""
        return [p.stem for p in self.user_dir.glob("*.enc")]

    def delete_secret(self, secret_type: str) -> bool:
        """
        Delete a specific secret.
        
        Returns
        -------
        bool
            True if secret was deleted, False if it didn't exist
        """
        secret_path = self._get_secret_path(secret_type)
        if secret_path.exists():
            secret_path.unlink()
            return True
        return False


class AuthService:

    def __init__(
        self,
        browser_manager: BrowserManager,
        db_api_url: str = "http://localhost:7999",
        session_duration: int = 7,
    ):
        """
        Initialize AuthService with database API connection.

        This service handles user authentication, session management, encryption, 
        and secure credential storage.

        Parameters
        ----------
        browser_manager : BrowserManager
            Instance of the browser manager.
        db_api_url : str
            URL of the database API service.
        session_duration : int
            Duration of session in days.
        """
        self._browser_manager = browser_manager
        self._db_api_url = db_api_url.rstrip('/')
        self._jwt_secret = os.getenv('JWT_SECRET', secrets.token_urlsafe(32))
        self._jwt_algorithm = 'HS256'
        self._session_duration = timedelta(days=session_duration)
        self._db_client = DatabaseClient(db_api_url=db_api_url)

    def _get_user_vault(self, user_id: str) -> UserVault:
        """Get or create a vault for the user."""
        return UserVault(user_id)

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

    def _initialize_vault(self, key_vault_path: Path) -> Fernet:
        """
        Initialize the encryption vault for a user.

        This method ensures that a unique encryption key is generated and stored for each user.
        If a key already exists in the vault file, it is loaded; otherwise, a new key is generated
        and stored securely.

        - The encryption key is essential for encrypting and decrypting sensitive user data.
        - If the vault file is missing, a new key is created and saved to the file.

        Parameters
        ----------
        session_token : str
            JWT session token.

        Returns
        -------
        bool
            True if the token is valid, False otherwise.
        """
        if not key_vault_path.exists():
            # Generate and save a new encryption key if the vault does not exist
            key = Fernet.generate_key()
            key_vault_path.write_bytes(key)
        else:
            # Read the existing key from the vault file
            key = key_vault_path.read_bytes()
        return Fernet(key)

    def _save_to_vault(self, user_id: str, key: str, value: str):
        """
        Securely store a key-value pair in the user's encrypted vault.

        This method encrypts and stores sensitive user data, such as passwords or API keys,
        in an encrypted vault file specific to each user.

        - The vault file is stored at a user-specific path.
        - Only encrypted data is stored, ensuring security.
        - This method overwrites existing data in the vault file.
        Parameters
        ----------
        user_id : str
            The unique identifier of the user.
        key : str
            The identifier for the credential being stored (e.g., "wg_password", "openai_key").
        value : str
            The sensitive data to be encrypted and saved.
        """
        vault_path = self._get_vault_path(user_id)
        cipher = self._initialize_vault(vault_path)

        # Save encrypted data
        data = {key: value}
        encrypted_data = cipher.encrypt(str(data).encode())
        vault_path.write_bytes(encrypted_data)

    def _load_from_vault(self, user_id: str, key: str) -> Optional[str]:
        """
        Retrieve a key-value pair from the user's encrypted vault.

        This method decrypts and retrieves user credentials or API keys securely stored
        in the vault.
        - If the vault does not exist or does not contain the requested key, returns None.
        - Only trusted data should be stored and accessed in the vault to prevent security risks.

        Parameters
        ----------
        user_id : str
            The unique identifier of the user.
        key : str
            The identifier of the credential to retrieve.

        Returns
        -------
        Optional[str]
            The decrypted value if found, otherwise None.

        Raises
        ------
        ValueError
            If the decryption process fails or stored data is corrupted.
        """
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
        """
        Get the file path to the user's encrypted key vault.

        This method ensures that a secure storage location is created for each user
        before returning the vault path.
        - The vault file is stored at `data/users/{user_id}/key_vault.enc`.
        - If the user's directory does not exist, it is created automatically.

        Parameters
        ----------
        user_id : str
            The unique identifier of the user.

        Returns
        -------
        Path
            The file path to the user's encrypted vault.
        """
        user_dir = Path(os.getenv("WORKINGDIR", "."), "data", "users", user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        return Path(user_dir, "key_vault.enc")

    def validate_session_token(self, session_token: str) -> bool:
        """
        Validate a JWT session token.

        This method decodes and verifies the session token to ensure it is valid and has not expired.

        - If the token is valid, it returns `True`, allowing continued authentication.
        - If the token is expired or invalid, it returns `False`.

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
        Extract the user ID from a session token.

        This method decodes the JWT session token and extracts the `user_id` associated
        with the session.

        - If the token is invalid or expired, an HTTP exception is raised.

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

    def _get_or_create_user(self, email: str):
        try:
            # Try to find existing user
            result = self._db_client.select(
                table="users",
                conditions=f"email = '{email}'",
            )

            if not result["success"]:
                raise HTTPException(status_code=500, detail="Database error")

            if not result["data"]:
                # Get max user ID for new user
                id_result = self._db_client.select(
                    table="users",
                    fields=["id"],
                )

                # Handle case when there are no users yet
                if not id_result["data"]:
                    user_id = "1"
                else:
                    user_id = str(max([user["id"] for user in id_result["data"]]) + 1)

                # Create new user
                user_data = {
                    "id": user_id,
                    "email": email,
                    "created_at": datetime.now().isoformat()
                }
                create_result = self._db_client.insert(
                    table="users",
                    data=user_data,
                )

                if not create_result["success"]:
                    raise HTTPException(status_code=500, detail="Failed to create user")
            else:
                user_id = str(result["data"][0]["id"])

            return user_id

        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def _create_session(self, user_id: int, session_token: str):
        """
        Create a new session in the database.
        
        Parameters
        ----------
        user_id : int
            The ID of the user for whom to create the session.
        session_token : str
            The session token to store.
            
        Returns
        -------
        dict
            The result of the database operation.
            
        Raises
        ------
        HTTPException
            If the session creation fails.
        """
        try:
            session_data = {
                "user_id": user_id,
                "token": session_token,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + self._session_duration).isoformat()
            }

            result = self._db_client.insert(
                table="sessions",
                data=session_data,
            )

            if not result["success"]:
                raise HTTPException(status_code=500,
                                    detail=f"Failed to create session: {result.get('error')}")
            return result

        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def _get_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Retrieve user data from the database.

        Parameters
        ----------
        user_id : str
            The unique identifier for the user.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing user data.

        Raises
        ------
        HTTPException
            If user is not found or database query fails.
        """
        try:
            result = self._db_client.select(
                table="users",
                conditions=f"id = '{user_id}'",
            )

            if not result["success"]:
                raise HTTPException(status_code=500,
                                    detail=f"Database error: {result.get('error')}")

            if not result["data"]:
                raise HTTPException(status_code=404, detail=f"User with ID {user_id} not found")

            return result["data"][0]

        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def authenticate_wg_gesucht(self, credentials: Dict[str, str]) -> AuthResponse:
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
            user_id = self._get_or_create_user(email)

            # Save WG-Gesucht password to the key vault
            # Store credentials in vault
            vault = self._get_user_vault(user_id)
            vault.store_secret(
                "wg_password",
                password,
            )

            # Generate a session token
            session_token = self._generate_session_token(user_id)
            session_result = self._create_session(
                user_id,
                session_token,
            )

            return AuthResponse(
                message="Successfully authenticated with WG-Gesucht",
                user_id=user_id,
                session_token=session_token,
            )

        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            self._browser_manager.close_user_browser(email)

    def authenticate_openai(
        self,
        session_token: str,
        credentials: OpenAICredentials,
    ) -> AuthResponse:
        """
        Authenticate and securely store the OpenAI API key for a user.

        This method validates the provided OpenAI API key by attempting an API request.
        If successful, the key is securely stored in the user's vault.

        - The OpenAI API key is verified before being stored to prevent invalid keys.
        - The API key is stored only in the vault and never in the database for security.

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
            openai_client = OpenAI(api_key=credentials.api_key)
            try:
                openai_client.models.list()
            except Exception:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid OpenAI API key",
                )

            # Save the API key securely to the user's key vault
            vault = self._get_user_vault(user_id)
            vault.store_secret("openai_key", credentials.api_key)

            return AuthResponse(
                user_id=user_id,
                session_token=session_token,
                message="Successfully stored OpenAI API key",
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_credentials(self, session_token: str) -> Dict[str, Any]:
        """
        Retrieve a user's credentials securely from the vault.

        This method retrieves stored user credentials, such as WG-Gesucht passwords and OpenAI API keys,
        by securely loading them from the encrypted vault. If any credentials are missing, an error is raised.

        - If the user does not exist in the database, a `404 Not Found` error is returned.
        - If credentials are missing in the vault, a `500 Internal Server Error` is raised.

        Parameters
        ----------
        session_token : str
            JWT session token for authentication.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing user's credentials.

        Raises
        ------
        HTTPException
            - 401 Unauthorized: If the session token is invalid.
            - 404 Not Found: If the user does not exist.
            - 500 Internal Server Error: If credentials are missing or retrieval fails.
        """
        try:
            # Extract user_id from the session token
            user_id = self.get_user_id(session_token)
            user_data = self._get_user_data(user_id)

            # Retrieve WG-Gesucht password from the key vault
            vault = self._get_user_vault(user_id)
            wg_password = vault.get_secret("wg_password")
            openai_key = vault.get_secret("openai_key")

            if not wg_password:
                # Not providing the openai key is okay if you don't want to use them
                raise HTTPException(status_code=500, detail="Missing required credentials in vault")

            return {
                "email": user_data["email"],
                "wg_password": wg_password,
                "openai_key": openai_key,
            }
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
