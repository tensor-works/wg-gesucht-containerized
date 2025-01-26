from fastapi import APIRouter, Depends, HTTPException
from selenium.webdriver.remote.webdriver import WebDriver
from typing import List, Optional
from ..dependencies import get_browser
from services.wg_gesucht_service import WGGesuchtService
from .models import SearchConfig, MessageRequest

router = APIRouter()

@router.get("/listings")
async def get_listings(
    search_config: SearchConfig,
    browser: WebDriver = Depends(get_browser)
) -> List[dict]:
    service = WGGesuchtService(browser)
    listings = await service.get_listings(search_config.dict())
    return listings

@router.get("/listing/{listing_ref}")
async def get_listing_details(
    listing_ref: str,
    browser: WebDriver = Depends(get_browser)
) -> dict:
    service = WGGesuchtService(browser)
    details = await service.get_listing_details(listing_ref)
    return details
