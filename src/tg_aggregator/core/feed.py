import asyncio
import logging
from datetime import datetime

from ..services.summarizer import generate_summary
from ..services.telethon_scraper import TelegramScraper
from ..types import FeedContent, Post

logger = logging.getLogger('news_aggregator')


class TelegramFeed:
    __slots__ = ('channel_id', 'channel_name', 'last_updated', 'content')
    _scraper_service: TelegramScraper = None

    def __init__(self, channel_id: int, channel_name: str):
        self.channel_id = channel_id
        self.channel_name = channel_name
        self.last_updated = None
        self.content: FeedContent = {
            'posts': {}
        }

        logger.info(f"[BaseFeed] {channel_id=} initialized")

    @classmethod
    def set_scraper_service(cls, scraper_service):
        cls._scraper_service = scraper_service

    @classmethod
    def get_scraper_service(cls):
        if cls._scraper_service is None:
            raise RuntimeError("Bot not set in TelegramFeed. Call TelegramFeed.set_scraper_service() first.")
        return cls._scraper_service

    async def _get_todays_posts(self):
        bot = self.get_scraper_service()
        try:
            messages = await bot.get_today_messages(channel_id=self.channel_id)
            logger.info(f"[BaseFeed] {len(messages)} messages received")
            updated_at = datetime.now()
            for message in messages['messages']:
                if message['id'] not in self.content['posts']:
                    message_data: Post = {}
                    message_data['updated_at'] = updated_at
                    message_data['text'] = message['text']
                    message_data['channel_id'] = self.channel_id
                    message_data['url'] = self._create_post_url(message['id'])
                    message_data['summary'] = None

                    self.content['posts'][message['id']] = message_data

            self.last_updated = messages['meta']['date']

        except Exception as e:
            logger.error(f"[TelegramFeed] Error updating {self.channel_id}: {str(e)}")

        finally:
            await bot.close()

    async def update(self):
        """Update the feed with new content from the Telegram channel"""
        logger.info(f"[TelegramFeed] Updating feed {self.channel_id} from channel {self.channel_id}")
        await self._get_todays_posts()
        await self._summarize_content()

    async def _summarize_content(self):
        async def summarize_wrapper(post_id, text):
            summary = await generate_summary(text)
            return post_id, summary

        logger.info(f"[TelegramFeed] Summarizing feed {self.channel_id}")

        tasks = []

        for post_id in self.content['posts'].keys():
            if self.content['posts'][post_id]['summary'] is None:
                text = self.content['posts'][post_id]['text']
                tasks.append(summarize_wrapper(post_id, text))

        results = await asyncio.gather(*tasks)

        for post_id, response in results:
            self.content['posts'][post_id]['summary'] = response.text

        logger.info(f"[TelegramFeed] Summarizing feed {self.channel_id} completed.")

    def _create_post_url(self, message_id: int):
        return f"https://t.me/{self.channel_name}/{message_id}"
