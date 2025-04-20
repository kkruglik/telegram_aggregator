from datetime import datetime, date
from typing import Dict, TypedDict, TypeVar, List

T = TypeVar("T")


class MetaMessages(TypedDict):
    channel_id: int
    date: date


class Message(TypedDict):
    id: int
    text: str


class ChannelMessages(TypedDict):
    meta: MetaMessages
    messages: List[Message]


class Post(TypedDict):
    updated_at: datetime
    text: str
    summary: str | None
    channel_id: int
    url: str


class FeedContent(TypedDict):
    posts: Dict[int, Post]
