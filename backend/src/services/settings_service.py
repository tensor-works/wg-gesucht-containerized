import os
from cryptography.fernet import Fernet

# Generate or load encryption key
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", Fernet.generate_key())
cipher = Fernet(ENCRYPTION_KEY)
stored_credentials = None

# Save credentials securely
def save_credentials(api_key: str, user_id: str):
    global stored_credentials
    credentials = f"{api_key}:{user_id}"
    encrypted_credentials = cipher.encrypt(credentials.encode())
    stored_credentials = encrypted_credentials

# Fetch profile photo (mock implementation)
def get_profile_photo() -> str:
    # Replace this with actual logic to fetch the photo URL
    return "https://example.com/path/to/profile-photo.jpg"

# Fetch OpenAI account balance
def get_openai_balance() -> float:
    if not stored_credentials:
        return None
    credentials = cipher.decrypt(stored_credentials).decode()
    api_key, _ = credentials.split(":")
    
    # Replace this with the actual OpenAI API call
    # Mock response
    return 42.00  # Example balance
