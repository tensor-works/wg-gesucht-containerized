# api/v1/wg_gesucht.py
from fastapi import APIRouter, Depends, HTTPException
from selenium.webdriver.remote.webdriver import WebDriver
from typing import List, Optional
from ..dependencies import get_browser
from services.wg_gesucht_service import WGGesuchtService
from .models import SearchConfig, MessageRequest

@router.post("/message/{listing_ref}")
async def send_message(
    listing_ref: str,
    message_request: MessageRequest,
    browser: WebDriver = Depends(get_browser)
) -> dict:
    service = WGGesuchtService(browser)
    
    # Check if already contacted
    if await service.check_previous_contact(listing_ref):
        raise HTTPException(status_code=400, detail="Already contacted this listing")
    
    success = await service.send_message(
        listing_ref, 
        message_request.message,
        message_request.template_data
    )
    
    return {"success": success}

@router.get("/messages")
async def get_messages(
    browser: WebDriver = Depends(get_browser)
) -> List[dict]:
    service = WGGesuchtService(browser)
    messages = await service.get_sent_messages()
    return messages