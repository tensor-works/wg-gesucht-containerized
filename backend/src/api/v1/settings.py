from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from services.settings_service import save_credentials, get_profile_photo, get_openai_balance
from typing import Optional

router = APIRouter()

class WGGesuchtCredentials(BaseModel):
    email: str
    password: str

class OpenAICredentials(BaseModel):
    api_key: str
    user_id: Optional[str] = None

class CredentialsRequest(BaseModel):
    credential_type: str  # 'wg_gesucht' or 'openai'
    wg_gesucht: Optional[WGGesuchtCredentials] = None
    openai: Optional[OpenAICredentials] = None

@router.post("/credentials")
def save_user_credentials(credentials: CredentialsRequest):
    try:
        if credentials.credential_type == "wg_gesucht" and credentials.wg_gesucht:
            # Save WG-Gesucht credentials
            # TODO: Implement WG-Gesucht specific storage
            return {"message": "WG-Gesucht credentials saved successfully"}
        
        elif credentials.credential_type == "openai" and credentials.openai:
            # Save OpenAI credentials
            save_credentials(credentials.openai.api_key, credentials.openai.user_id or "default")
            return {"message": "OpenAI credentials saved successfully"}
        
        else:
            raise HTTPException(status_code=400, detail="Invalid credential type or missing data")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ProfilePhotoResponse(BaseModel):
    photo_url: str

class OpenAIBalanceResponse(BaseModel):
    balance: float


@router.get("/profile-photo", response_model=ProfilePhotoResponse)
def fetch_profile_photo():
    photo_url = get_profile_photo()
    if not photo_url:
        raise HTTPException(status_code=404, detail="Profile photo not found")
    return {"photo_url": photo_url}

@router.get("/openai-balance", response_model=OpenAIBalanceResponse)
def fetch_openai_balance():
    balance = get_openai_balance()
    if balance is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve OpenAI balance")
    return {"balance": balance}
