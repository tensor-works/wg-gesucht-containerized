from services.base_service import BaseWGGesuchtService

class MessageService(BaseWGGesuchtService):
    async def send_message(self, listing_ref: str, message: str):
        await self.ensure_logged_in()
        # Message sending logic
        
    async def get_sent_messages(self):
        await self.ensure_logged_in()