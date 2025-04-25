import aiohttp
from ..config import SCRAPER_URL


async def get_channel_id(feed_name: str, service_url: str = None) -> tuple[int, str]:
    """Make a simple request to get channel ID from the scraper service"""
    service_url = service_url or SCRAPER_URL

    if service_url is None:
        raise ValueError("No service urk provided")

    async with aiohttp.ClientSession() as session:
        url = f"{service_url}/channel_id"
        payload = {"channel": feed_name}

        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to get channel ID: {error_text}")

            data = await response.json()
            return data["channel_id"], data.get("username", "")


async def get_today_messages_by_channel_id(channel_id: int, service_url: str = None):
    """Get today's messages for a channel from the scraper service"""
    service_url = service_url or SCRAPER_URL

    if service_url is None:
        raise ValueError("No service urk provided")

    async with aiohttp.ClientSession() as session:
        url = f"{service_url}/messages_by_id"
        payload = {"channel_id": channel_id}

        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to get messages: {error_text}")

            return await response.json()


async def get_today_messages_by_channel_name(channel_name: str, service_url: str = None):
    """Get today's messages for a channel from the scraper service"""
    service_url = service_url or SCRAPER_URL

    if service_url is None:
        raise ValueError("No service urk provided")

    async with aiohttp.ClientSession() as session:
        url = f"{service_url}/messages_by_name"
        payload = {"channel_name": channel_name}

        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to get messages: {error_text}")

            return await response.json()
