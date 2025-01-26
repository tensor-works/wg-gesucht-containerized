from services.base_service import BaseWGGesuchtService
from listing_getter import ListingGetter
from listing_info_getter import ListingInfoGetter

class ListingService(BaseWGGesuchtService):
    async def get_listings(self, search_config: dict):
        await self.ensure_logged_in()
        listing_getter = ListingGetter(search_config["url"])
        return listing_getter.get_all_infos()
        
    async def get_listing_details(self, listing_ref: str):
        await self.ensure_logged_in()
        info_getter = ListingInfoGetter(listing_ref)
        return {
            "text": info_getter.get_listing_text(),
            "rental_length": info_getter.get_rental_length_months()
        }