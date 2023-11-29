from typing import Optional
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from czytacz import models, schemas, FeedStatus


class NotFoundError(Exception):
    pass


class AlreadyFetchingError(Exception):
    pass


def get_user_feeds(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
) -> list[schemas.FeedForList]:
    feeds = db.execute(
        select(models.Feed)
        .where(models.Feed.user_id == user_id)
        .offset(skip)
        .limit(limit)
    ).scalars()
    return [schemas.FeedForList.from_orm(feed) for feed in feeds]


def get_feed(
    db: Session, user_id: int, feed_id: int, read: Optional[bool] = None, skip: int = 0, limit: int = 100
) -> schemas.Feed:
    feed = db.execute(
        select(models.Feed).where(
            models.Feed.user_id == user_id, models.Feed.id == feed_id
        )
    ).scalar_one_or_none()
    if feed is None:
        raise NotFoundError()

    items_query = select(models.Item).where(models.Item.feed_id == feed.id)
    
    if read is not None:
        items_query = items_query.where(models.Item.read == read)
    items = db.execute(
        items_query
        .order_by(models.Item.updated.desc())
    ).scalars()

    return schemas.Feed(
        id=feed.id,
        user_id=feed.user_id,
        name=feed.name,
        source=schemas.PublicUrl(
            feed.actual_source if feed.actual_source is not None else feed.source
        ),
        status=feed.status,
        last_fetch=feed.last_fetch,
        items=[schemas.Item.from_orm(item) for item in items],
    )


def update_item(
    db: Session,
    user_id: int,
    feed_id: int,
    item_id: int,
    details: schemas.ItemForUpdate,
) -> schemas.Item:
    item = db.execute(
        select(models.Item)
        .join(models.Feed)
        .join(models.User)
        .where(
            models.User.id == user_id, models.Feed.id == feed_id, models.Item.id == item_id
        )
    ).scalar_one_or_none()
    if item is None:
        raise NotFoundError()

    if details.read is not None:
        item.read = details.read

    db.add(item)
    db.commit()
    db.refresh(item)
    return schemas.Item.from_orm(item)


def create_user_feed(
    db: Session, feed: schemas.FeedCreate, user_id: int
) -> schemas.Feed:
    db_feed = models.Feed(**feed.model_dump(), user_id=user_id)
    db.add(db_feed)
    db.commit()
    db.refresh(db_feed)
    return schemas.Feed.from_orm(db_feed)


def delete_user_feed(db: Session, user_id: int, feed_id: int):
    rows = db.execute(
        delete(models.Feed).where(
            models.Feed.user_id == user_id, models.Feed.id == feed_id
        )
    ).rowcount

    if rows == 0:
        raise NotFoundError()
    db.commit()


def force_fetch(db: Session, user_id: int, feed_id: int):
    from czytacz import tasks

    feed = db.execute(
        select(models.Feed)
        .where(models.Feed.user_id == user_id, models.Feed.id == feed_id)
        .with_for_update()
    ).scalar_one_or_none()
    if feed is None:
        raise NotFoundError()
    if feed.status == FeedStatus.FETCHING:
        raise AlreadyFetchingError()

    tasks.fetch_feed.delay(feed.id, True)
