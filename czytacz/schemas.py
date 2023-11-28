from __future__ import annotations

import datetime
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


class ItemCreate(ItemBase):
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


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    feeds: list[Feed] = []

    class Config:
        from_attributes = True
