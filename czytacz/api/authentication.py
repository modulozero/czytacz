from typing import Annotated, Optional

from argon2 import PasswordHasher
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from psycopg.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from czytacz import dependencies, models, schemas

security = HTTPBasic()


class EmailAlreadyUsedError(Exception):
    pass


def create_user(
    db: Session,
    password_hasher: PasswordHasher,
    user: schemas.UserCreate,
):
    hashed_password = password_hasher.hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
    )
    db.add(db_user)

    try:
        db.commit()
    except IntegrityError as e:
        if isinstance(e.orig, UniqueViolation):
            raise EmailAlreadyUsedError
        raise

    db.refresh(db_user)
    return schemas.User.from_orm(db_user)


def authenticate_user(
    db: Session, password_hasher: PasswordHasher, email: str, password: str
) -> Optional[schemas.User]:
    user_db = db.query(models.User).filter(models.User.email == email).one_or_none()

    if user_db is None or user_db.hashed_password is None:
        return None

    if password_hasher.verify(user_db.hashed_password, password):
        return schemas.User.from_orm(user_db)

    return None


def get_current_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
    db: dependencies.DatabaseSession,
    password_hasher: dependencies.PasswordHasher,
) -> Optional[schemas.User]:
    return authenticate_user(
        db, password_hasher, credentials.username, credentials.password
    )


CurrentUser = Annotated[Optional[schemas.User], Depends(get_current_user)]


def require_user(current_user: CurrentUser) -> schemas.User:
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return current_user


RequireUser = Annotated[schemas.User, Depends(require_user)]
