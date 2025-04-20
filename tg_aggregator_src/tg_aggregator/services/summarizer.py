import logging
from asyncio import Semaphore

from google import genai
from google.genai import types

from tg_aggregator_src.tg_aggregator.config import GEMINI_API_KEY
from tg_aggregator_src.tg_aggregator.services.prompt import prompt as system_prompt

logger = logging.getLogger('news_aggregator')

client = genai.Client(api_key=GEMINI_API_KEY)

semaphore = Semaphore(value=10)


async def generate_summary(input_text: str):
    logger.info(f"Generating summary for input: {input_text}")
    prompt = system_prompt.format(input_text=input_text)
    async with semaphore:
        try:
            response = await client.aio.models.generate_content(
                model='gemini-2.0-flash-lite',
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=1000,
                    temperature=0.2,
                )
            )
        except Exception as e:
            logger.error(e, exc_info=True)
    return response
