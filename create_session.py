import asyncio
import os

from telethon.sync import TelegramClient


async def main():
    api_id = int(os.environ["API_ID"])
    api_hash = os.environ["API_HASH"]
    session_name = os.environ.get("SESSION_NAME", "telegram_scraper")

    async with TelegramClient(session_name, api_id, api_hash) as client:
        await client.start()
        print(f"Session saved to {session_name}.session")


asyncio.run(main())
