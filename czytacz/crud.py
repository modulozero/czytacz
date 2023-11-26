from argon2 import PasswordHasher
from sqlalchemy.orm import Session

from . import models, schemas


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).one_or_none()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).one_or_none()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    ph = PasswordHasher()
    hashed_password = ph.hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_feeds(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Feed).offset(skip).limit(limit).all()


def create_user_feed(db: Session, feed: schemas.FeedCreate, user_id: int):
    db_feed = models.Feed(**feed.model_dump(), user_id=user_id)
    db.add(db_feed)
    db.commit()
    db.refresh(db_feed)
    return db_feed
