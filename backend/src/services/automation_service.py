from services.listing_service import ListingService
from services.message_service import MessageService
from selenium.webdriver.remote.webdriver import WebDriver


class AutomationService:
    def __init__(self, browser: WebDriver):
        self.listing_service = ListingService(browser)
        self.message_service = MessageService(browser)
        
    async def run_automation(self, search_config: dict, message_template: str):
        # Get new listings using listing service
        listings = await self.listing_service.get_listings(search_config)
        
        for listing in listings:
            # Get details using listing service
            details = await self.listing_service.get_listing_details(listing["ref"])
            
            # Send message using message service
            await self.message_service.send_message(listing["ref"], message_template)