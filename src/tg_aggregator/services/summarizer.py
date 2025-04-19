import logging
from asyncio import Semaphore

from google import genai
from google.genai import types

from src.tg_aggregator.config import GEMINI_API_KEY

logger = logging.getLogger('news_aggregator')

client = genai.Client(api_key=GEMINI_API_KEY)

semaphore = Semaphore(value=10)


async def generate_summary(input_text: str):
    prompt = f'Сделай короткое саммари этого текста. Используй не больше пяти преложений. Если текст короткий, то оставь его таким какой он есть: {input_text}'
    response = 'your summary'
    async with semaphore:
        try:
            response = await client.aio.models.generate_content(
                model='gemini-2.0-flash-lite',
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=500,
                    temperature=0.1
                )
            )
        except Exception as e:
            logger.error(e, exc_info=True)
    return response
