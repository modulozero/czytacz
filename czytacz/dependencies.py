from contextlib import contextmanager
from functools import lru_cache
from typing import Annotated, Callable, Generator

import argon2
from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from czytacz.settings import Settings


@lru_cache
def get_settings() -> Settings:
    return Settings() # type: ignore


def get_session_factory(settings: Annotated[Settings, Depends(get_settings)]):
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db(
    session_factory: Annotated[Callable, Depends(get_session_factory)]
) -> Generator[Session, None, None]:
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


DatabaseSession = Annotated[Session, Depends(get_db)]


@contextmanager
def get_db_cli() -> Generator[Session, None, None]:
    """Acquire a session in a manner that's useful without FastAPI's DI.

    In CLI, we don't have access to FastAPI's DI, so we'd have to assemble
    all of this in the caller. That's even more awkward than having a CLI
    specific function here.

    It's a bit annoying, and I'm sure I can remove the duplication -
    but for now I'm focusing on other issues.
    """
    session_factory = get_session_factory(get_settings())
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def get_password_hasher() -> argon2.PasswordHasher:
    return argon2.PasswordHasher()


PasswordHasher = Annotated[argon2.PasswordHasher, Depends(get_password_hasher)]
