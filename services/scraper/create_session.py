import asyncio
from telethon.sync import TelegramClient

API_ID = 24801971
API_HASH = "764bbe046683e2884129d588cb7be5c2"
SESSION_NAME = "telegram_scraper.session"


async def main():
    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        await client.start()


asyncio.run(main())
