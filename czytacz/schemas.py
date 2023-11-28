from __future__ import annotations

import datetime
import enum
from typing import Optional

from pydantic import BaseModel


class ItemContent(BaseModel):
    content_type: str
    value: Optional[str]


class ItemBase(BaseModel):
    item_id: str
    title: Optional[str]
    link: Optional[str]
    author: Optional[str]
    summary: Optional[str]
    published: Optional[datetime.datetime]
    content: list[ItemContent] = []


class ItemFetched(ItemBase):
    pass


class Item(ItemBase):
    class Config:
        from_attributes = True


class FeedBase(BaseModel):
    name: str
    source: str


class FeedCreate(FeedBase):
    pass


class Feed(FeedBase):
    id: int
    user_id: int

    items: list[Item] = []

    class Config:
        from_attributes = True


class FeedForFetch(FeedBase):
    id: int
    source: str
    etag: Optional[str]
    last_modified: Optional[str]

    class Config:
        from_attributes = True


class FeedFetchStatus(enum.Enum):
    FETCHED = enum.auto()
    PERMANENT_REDIRECT = enum.auto()
    NO_CHANGE = enum.auto()
    GONE = enum.auto()
    GENERIC_ERROR = enum.auto()

    @property
    def ok(self) -> bool:
        """Indicates that feed fetch was okay."""
        return self in [self.FETCHED, self.PERMANENT_REDIRECT, self.NO_CHANGE]

    @property
    def update(self) -> bool:
        """Indicates whether the feed should be updated in any way."""
        return self in [self.PERMANENT_REDIRECT, self.FETCHED]


class FeedFetchResult(BaseModel):
    source: str
    status: FeedFetchStatus
    etag: Optional[str]
    last_modified: Optional[str]
    items: list[ItemFetched] = []


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    feeds: list[Feed] = []

    class Config:
        from_attributes = True
