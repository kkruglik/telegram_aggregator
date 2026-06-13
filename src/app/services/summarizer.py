from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from typing import Annotated, Protocol
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
import logging
from asyncio import Semaphore
from ..config import config

logger = logging.getLogger("news_aggregator")


semaphore = Semaphore(value=10)


class SummaryModel(BaseModel):
    reasoning: Annotated[
        str, Field(..., description="One sentence explaining the summarization decision.")
    ]
    summary: Annotated[
        str,
        Field(
            ...,
            description="Bullet-point summary of the input text, each bullet starting with '—'.",
        ),
    ]
    tags: Annotated[
        list[str], Field(..., description="3-5 short topic tags extracted from the text.")
    ]


class SummarizeProtocol(Protocol):
    async def generate(self, user_messages: str) -> SummaryModel: ...


class OpenAISummarizer:
    def __init__(
        self,
        token: str,
        system_prompt: str,
        model_name: str,
        temperature: float,
    ):
        self.client = AsyncOpenAI(api_key=token)
        self.model = model_name
        self.temperature = temperature
        self.system_prompt = system_prompt

    # TODO: add retry logic
    async def generate(self, user_messages: str) -> SummaryModel:
        logger.info(f"Generating summary, input_length={len(user_messages)}")

        messages = []
        messages.append(ChatCompletionSystemMessageParam(role="system", content=self.system_prompt))
        messages.append(ChatCompletionUserMessageParam(role="user", content=user_messages))

        async with semaphore:
            response = await self.client.beta.chat.completions.parse(
                model=self.model,
                messages=messages,
                response_format=SummaryModel,
                temperature=self.temperature,
            )

        usage = response.usage

        logger.info(
            f"Summary generated, tokens=({usage.prompt_tokens if usage else 'unk'} prompt / {usage.completion_tokens if usage else 'unk'} completion)"
        )

        msg = response.choices[0].message

        if msg.refusal:
            raise ValueError(f"Model refused: {msg.refusal}")

        if msg.parsed is None:
            raise ValueError("Structured output parsing returned None")

        return msg.parsed


summarizer_client = OpenAISummarizer(
    token=config.openai.token,
    system_prompt=config.openai.system_prompt,
    model_name=config.openai.model_name,
    temperature=config.openai.temperature,
)
