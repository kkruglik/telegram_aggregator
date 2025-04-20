import aiohttp


async def get_channel_id(feed_name: str, service_url: str = "http://localhost:8000") -> tuple[int, str]:
    """Make a simple request to get channel ID from the scraper service"""
    async with aiohttp.ClientSession() as session:
        url = f"{service_url}/channel_id"
        payload = {"channel": feed_name}

        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to get channel ID: {error_text}")

            data = await response.json()
            return data["channel_id"], data.get("username", "")


async def get_today_messages(channel_id: int, service_url: str = "http://localhost:8000"):
    """Get today's messages for a channel from the scraper service"""
    async with aiohttp.ClientSession() as session:
        url = f"{service_url}/messages"
        payload = {"channel_id": channel_id}

        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Failed to get messages: {error_text}")

            return await response.json()
