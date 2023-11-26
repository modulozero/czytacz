from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "user"

    id = mapped_column(Integer, primary_key=True)

    email: Mapped[str]
    hashed_password: Mapped[Optional[str]]

    feeds: Mapped[list["Feed"]] = relationship(back_populates="user")


class Feed(Base):
    __tablename__ = "feed"

    id = mapped_column(Integer, primary_key=True)
    user_id = mapped_column(ForeignKey("user.id"))
    name: Mapped[str]
    source: Mapped[str]

    user: Mapped[User] = relationship(back_populates="feeds")
