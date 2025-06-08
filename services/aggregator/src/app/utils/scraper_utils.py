import logging

import aiohttp  # type: ignore

logger = logging.getLogger("news_aggregator")


async def get_channel_id(feed_name: str, service_url: str) -> tuple[int | None, str]:
    """Make a simple request to get channel ID from the scraper service"""
    async with aiohttp.ClientSession() as session:
        url = f"{service_url}/channel_id"
        payload = {"channel": feed_name}

        try:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["channel_id"], data.get("username", "")

                if response.status in [404, 422, 500]:
                    error_text = await response.text()
                    logger.warning(f"Channel {feed_name} not found: {error_text}")
                    return None, ""

                error_text = await response.text()
                logger.error(f"Unexpected HTTP {response.status} from scraper: {error_text}")
                return None, ""

        except aiohttp.ClientError as e:
            logger.error(f"Network error contacting scraper service: {e}")
            return None, ""
        except Exception as e:
            logger.error(f"Unexpected error in get_channel_id: {e}")
            return None, ""


async def get_today_messages_by_channel_id(channel_id: int, service_url: str):
    """Get today's messages for a channel from the scraper service"""
    async with aiohttp.ClientSession() as session:
        url = f"{service_url}/messages_by_id"
        payload = {"channel_id": channel_id}

        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to get messages: {error_text}")

            return await response.json()


async def get_today_messages_by_channel_name(channel_name: str, service_url: str):
    """Get today's messages for a channel from the scraper service"""
    async with aiohttp.ClientSession() as session:
        url = f"{service_url}/messages_by_name"
        payload = {"channel_name": channel_name}

        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to get messages: {error_text}")

            return await response.json()
