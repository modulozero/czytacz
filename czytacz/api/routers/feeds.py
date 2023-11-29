from typing import Optional
from fastapi import APIRouter, HTTPException, status

from czytacz import dependencies, feeds, schemas
from czytacz.api import authentication

router = APIRouter()


@router.post("/feeds/", response_model=schemas.Feed)
def subscribe_feed(
    db: dependencies.DatabaseSession,
    user: authentication.RequireUser,
    feed: schemas.FeedCreate,
):
    return feeds.create_user_feed(db=db, feed=feed, user_id=user.id)


@router.get("/feeds/", response_model=list[schemas.FeedForList])
def list_feeds(
    db: dependencies.DatabaseSession,
    user: authentication.RequireUser,
    skip: int = 0,
    limit: int = 100,
):
    items = feeds.get_user_feeds(db, user_id=user.id, skip=skip, limit=limit)
    return items


@router.get("/feeds/{feed_id}", response_model=schemas.Feed)
def show_feed(
    db: dependencies.DatabaseSession,
    user: authentication.RequireUser,
    feed_id: int,
    read: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
):
    try:
        feed = feeds.get_feed(
            db, feed_id=feed_id, user_id=user.id, read=read, skip=skip, limit=limit
        )
    except feeds.NotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    return feed


@router.delete("/feeds/{feed_id}")
def delete_feed(
    db: dependencies.DatabaseSession,
    user: authentication.RequireUser,
    feed_id: int,
):
    try:
        feeds.delete_user_feed(db, user_id=user.id, feed_id=feed_id)
    except feeds.NotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND)


@router.post("/feeds/{feed_id}/force_fetch")
def force_fetch(
    db: dependencies.DatabaseSession,
    user: authentication.RequireUser,
    feed_id: int,
):
    try:
        feeds.force_fetch(db, user_id=user.id, feed_id=feed_id)
    except feeds.NotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    except feeds.AlreadyFetchingError:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, detail="Already fetching the feed"
        )


@router.put("/feeds/{feed_id}/{item_id}")
def update_item(
    db: dependencies.DatabaseSession,
    user: authentication.RequireUser,
    feed_id: int,
    item_id: int,
    item: schemas.ItemForUpdate,
) -> schemas.Item:
    try:
        updated_item = feeds.update_item(db, user.id, feed_id, item_id, item)
    except feeds.NotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    return updated_item
