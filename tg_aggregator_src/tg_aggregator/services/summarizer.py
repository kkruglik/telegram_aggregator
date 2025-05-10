import logging
from asyncio import Semaphore

from google.genai import types

from tg_aggregator_src.tg_aggregator.services.prompt import prompt as system_prompt

logger = logging.getLogger("news_aggregator")


semaphore = Semaphore(value=10)


async def generate_summary(client, input_text: str):
    logger.info(f"Generating summary for input: {input_text}")
    prompt = system_prompt.format(input_text=input_text)
    async with semaphore:
        try:
            response = await client.aio.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=1000,
                    temperature=0.4,
                ),
            )
        except Exception as e:
            logger.error(e, exc_info=True)
    return response
