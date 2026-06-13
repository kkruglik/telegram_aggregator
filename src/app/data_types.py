from datetime import date, datetime
from typing import TypedDict, TypeVar

T = TypeVar("T")


class MetaMessages(TypedDict):
    channel_id: int
    date: date


class Message(TypedDict):
    id: int
    text: str


class ChannelMessages(TypedDict):
    meta: MetaMessages
    messages: list[Message]


class Post(TypedDict):
    updated_at: datetime
    text: str
    summary: str | None
    channel_id: int
    url: str
    id: int


class FeedContent(TypedDict):
    posts: dict[int, Post]
