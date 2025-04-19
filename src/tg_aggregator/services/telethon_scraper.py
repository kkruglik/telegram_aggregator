import logging
from telethon import TelegramClient
from datetime import datetime

from ..types import ChannelMessages

logger = logging.getLogger('news_aggregator')

class TelegramScraper:
    def __init__(self, api_id: int, api_hash: str, session_name: str = "telegram_scraper"):
        self.client = TelegramClient(session_name, api_id, api_hash)

    async def get_today_messages(self, channel_id: int) -> ChannelMessages:
        logger.info(f"Getting today messages for channel {channel_id}")
        await self.client.start()

        today = datetime.now(tz=None).date()
        messages: ChannelMessages = {
            'meta':{'channel_id': channel_id, 'date': datetime.now(tz=None), },
            'messages': [],
        }

        async for message in self.client.iter_messages(channel_id):
            if message.date.date() < today:
                break
            message_text = message.text
            if message_text is None or message_text == '':
                continue

            messages['messages'].append({'id': message.id, 'text': message_text})
        return messages

    async def close(self):
        logger.info('Closing Telegram Scraper')
        await self.client.disconnect()

    async def get_channel_id(self, channel: str) -> tuple[int, str]:
        # TODO add check if its a channel and raise error if its not
        logger.info(f"Getting channel ID for channel {channel}")

        await self.client.start()

        try:
            entity = await self.client.get_entity(channel)
            channel_id = entity.id
            username = entity.username

            # For supergroups/channels, we need to get the negative ID
            if hasattr(entity, 'megagroup') or hasattr(entity, 'broadcast'):
                # Convert to channel ID format with -100 prefix
                channel_id = int(f"-100{channel_id}")

            logger.info(f"Found channel ID: {channel_id}")
            return channel_id, username

        except Exception as e:
            logger.error(f"Error getting channel ID for {channel}: {str(e)}")
            raise
