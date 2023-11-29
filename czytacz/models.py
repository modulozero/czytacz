from __future__ import annotations

import datetime
from typing import Any, Optional

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from czytacz import FeedStatus
from czytacz.database import Base


class User(Base):
    """User represents agents interacting with the reader."""

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    email: Mapped[str]
    # Hashed_password is optional, allowing for "locked out" users.
    hashed_password: Mapped[Optional[str]]

    feeds: Mapped[list[Feed]] = relationship(back_populates="user")


class Feed(Base):
    """A feed that the user wants to subscribe to."""

    __tablename__ = "feed"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    name: Mapped[str]

    source: Mapped[str]
    # I want to maintain what user gave us initially, but hitting the URL in
    # case of a 301 is a bad idea.
    actual_source: Mapped[Optional[str]]

    user: Mapped[User] = relationship(back_populates="feeds")
    items: Mapped[list[Item]] = relationship(
        back_populates="feed", cascade="all, delete", passive_deletes=True
    )

    # Used for interaction with the server, and returned as-is to it
    etag: Mapped[Optional[str]]
    last_modified: Mapped[Optional[str]]

    status: Mapped[Optional[FeedStatus]]
    last_fetch: Mapped[Optional[datetime.datetime]]

class Item(Base):
    """An item from a feed.

    The contents of the post are extracted using feedparser,
    """

    __tablename__ = "item"
    __table_args__ = (UniqueConstraint("feed_id", "item_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    feed_id: Mapped[int] = mapped_column(ForeignKey("feed.id", ondelete="CASCADE"))
    feed: Mapped[Feed] = relationship(back_populates="items")

    # This is separate from the primary key for the following reasons:
    # - it's assigned by the feed processor, and could conceivably change.
    # - I'm always hesitant about "natural" primary keys
    # - while writing this part I am still considering that this field might
    #   end up optional, and replaced by something entirely different.
    item_id: Mapped[Optional[str]] = mapped_column(String, unique=True)

    first_seen: Mapped[datetime.datetime]
    """
    Always present field that indicates when we have seen an item with this ID
    """

    title: Mapped[Optional[str]]
    link: Mapped[Optional[str]]
    author: Mapped[Optional[str]]
    summary: Mapped[Optional[str]]
    published: Mapped[Optional[datetime.datetime]]
    content: Mapped[list[Any]] = mapped_column(JSONB)
    updated: Mapped[datetime.datetime]
    read: Mapped[bool] = mapped_column(default=False)
