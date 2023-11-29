from __future__ import annotations

import datetime
import enum
from typing import Optional, Annotated

from pydantic import BaseModel, HttpUrl, AfterValidator

import tldextract
from czytacz import FeedStatus


def ensure_public(url: HttpUrl) -> HttpUrl:
    # This can be sometimes slow
    extracted = tldextract.extract(str(url), include_psl_private_domains=True)
    assert not extracted.is_private, f"{url} is not a public URL"
    assert bool(extracted.suffix), f"{url} doesn't have a suffix"
    assert bool(extracted.domain), f"{url} doesn't have a domain"
    assert bool(extracted.fqdn), f"{url} is not an fqdn"

    return url


PublicUrl = Annotated[HttpUrl, AfterValidator(ensure_public)]


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
    updated: Optional[datetime.datetime]


class Item(ItemBase):
    updated: datetime.datetime

    class Config:
        from_attributes = True


class FeedBase(BaseModel):
    name: Optional[str]
    source: PublicUrl


class FeedCreate(FeedBase):
    pass


class Feed(FeedBase):
    id: int
    user_id: int
    status: Optional[FeedStatus]
    last_fetch: Optional[datetime.datetime]

    items: list[Item] = []

    class Config:
        from_attributes = True


class FeedForFetch(FeedBase):
    id: int
    etag: Optional[str]
    last_modified: Optional[str]

    class Config:
        from_attributes = True


class FeedForList(FeedBase):
    id: int
    status: FeedStatus
    last_fetch: datetime.datetime

    class Config:
        from_attributes = True


class FeedFetchStatus(enum.Enum):
    FETCHED = enum.auto()
    PERMANENT_REDIRECT = enum.auto()
    NO_CHANGE = enum.auto()
    GONE = enum.auto()
    GENERIC_ERROR = enum.auto()
    TRY_LATER = enum.auto()

    @property
    def ok(self) -> bool:
        """Indicates that feed fetch was okay."""
        return self in [self.FETCHED, self.PERMANENT_REDIRECT, self.NO_CHANGE]

    @property
    def update(self) -> bool:
        """Indicates whether the feed should be updated in any way."""
        return self in [self.PERMANENT_REDIRECT, self.FETCHED]


class FeedFetchResult(BaseModel):
    source: PublicUrl
    status: FeedFetchStatus
    etag: Optional[str]
    last_modified: Optional[str]
    items: list[ItemFetched] = []


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int

    class Config:
        from_attributes = True
