import logging
from asyncio import Semaphore

from google.genai import types  # type: ignore

from .prompt import prompt_v1_2

logger = logging.getLogger("news_aggregator")


semaphore = Semaphore(value=10)


async def generate_summary(client, input_text: str):
    logger.info(f"Generating summary for input: {input_text}")
    prompt = prompt_v1_2.format(input_text=input_text)
    async with semaphore:
        try:
            response = await client.aio.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(max_output_tokens=1200, temperature=0.2),
            )
        except Exception as e:
            logger.error(e, exc_info=True)
    return response
