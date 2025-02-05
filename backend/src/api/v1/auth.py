from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from services.auth_service import (
    AuthService,
    WGGesuchtCredentials,
    OpenAICredentials,
)
from utils.browser_manager import BrowserManager
from dotenv import load_dotenv

load_dotenv()

# Initialize FastAPI
app = FastAPI(title="Auth Service API")
browser_manager = BrowserManager()
auth_service = AuthService(browser_manager)


@app.get("/health")
async def health_check():
    """Health check endpoint for Auth Service."""
    try:
        return {"status": "healthy", "auth_service": "operational"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.post("/authenticate/wg-gesucht")
async def authenticate_wg_gesucht(credentials: WGGesuchtCredentials):
    """Authenticate with WG-Gesucht and return session token."""
    result = auth_service.authenticate_wg_gesucht(credentials.dict())
    return result


@app.post("/authenticate/openai")
async def authenticate_openai(session_token: str, credentials: OpenAICredentials):
    """Authenticate and store OpenAI API key."""
    try:
        result = auth_service.authenticate_openai(session_token, credentials)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/validate-token")
async def validate_token(session_token: str):
    """Validate a session token."""
    is_valid = auth_service.validate_session_token(session_token)
    return {"valid": is_valid}


@app.get("/get-credentials")
async def get_credentials(session_token: str):
    """Retrieve user credentials securely."""
    result = auth_service.get_credentials(session_token)
    return result


@app.delete("/delete-credentials")
async def delete_credentials(
    session_token: str,
    key: str,
):
    """Delete a specific credential from the user's vault."""
    user_id = auth_service.get_user_id(session_token)
    vault = auth_service._get_user_vault(user_id)
    success = vault.delete_secret(key)

    if not success:
        raise HTTPException(status_code=404, detail="Credential not found")

    return {"message": f"Successfully deleted {key}"}


@app.get("/get-user-id")
async def get_user_id(session_token: str):
    """Extract user ID from a session token."""
    try:
        return {"user_id": auth_service.get_user_id(session_token)}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
