from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.profile_service import ProfileService
from utils.browser_manager import BrowserManager
from dotenv import load_dotenv

load_dotenv()

# Initialize FastAPI
app = FastAPI(title="Profile Service API")

# Initialize services
browser_manager = BrowserManager()
profile_service = ProfileService(browser_manager)


# Response models
class PhotoResponse(BaseModel):
    photo_url: str


class NameResponse(BaseModel):
    first_name: str
    last_name: str


class AddressResponse(BaseModel):
    city: str
    postal_code: str
    street_and_house_number: str


class PhotoDownloadResponse(BaseModel):
    photo_path: str


@app.get("/health")
async def health_check():
    """Health check endpoint for Profile Service."""
    try:
        return {"status": "healthy", "profile_service": "operational"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.get("/profile/photo", response_model=PhotoResponse)
async def get_profile_photo(session_token: str):
    """Get user's profile photo URL."""
    try:
        photo_url = profile_service.get_profile_photo(session_token)
        return {"photo_url": photo_url}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/profile/name", response_model=NameResponse)
async def get_profile_name(session_token: str):
    """Get user's name details."""
    try:
        name_data = profile_service.get_profile_name(session_token)
        return name_data
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/profile/address", response_model=AddressResponse)
async def get_profile_address(session_token: str):
    """Get user's address details."""
    try:
        address_data = profile_service.get_user_address(session_token)
        return address_data
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/profile/photo/download", response_model=PhotoDownloadResponse)
async def download_profile_photo(session_token: str, save_path: Optional[str] = None):
    """Download user's profile photo."""
    try:
        photo_path = profile_service.download_profile_photo(session_token, save_path)
        return {"photo_path": photo_path}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
