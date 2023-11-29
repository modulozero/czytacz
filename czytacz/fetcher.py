import datetime
from typing import Any, Optional

import feedparser
from sqlalchemy import select
from sqlalchemy.orm import Session

from czytacz import models, schemas, FeedStatus


class FeedNotFoundError(Exception):
    pass


def process_item(feed_item: Any) -> schemas.ItemFetched:
    published_parsed = feed_item.get("published_parsed")
    updated_parsed = feed_item.get("updated_parsed")
    return schemas.ItemFetched(
        item_id=feed_item.id,
        title=feed_item.get("title"),
        link=feed_item.get("link"),
        author=feed_item.get("author"),
        summary=feed_item.get("summary"),
        published=(
            datetime.datetime(*published_parsed[:6])
            if published_parsed is not None
            else None
        ),
        updated=(
            datetime.datetime(*updated_parsed[:6])
            if updated_parsed is not None
            else None
        ),
        content=[
            schemas.ItemContent(
                content_type=feed_content.type,
                value=feed_content.value,
            )
            for feed_content in feed_item.get("content", [])
        ],
    )


def fetch_feed(
    feed: schemas.FeedForFetch, force_fetch: bool = False
) -> schemas.FeedFetchResult:
    if force_fetch:
        parsed = feedparser.parse(str(feed.source))
    else:
        parsed = feedparser.parse(
            str(feed.source), etag=feed.etag, modified=feed.last_modified
        )

    return schemas.FeedFetchResult(
        source=parsed.href,
        etag=parsed.get("etag"),
        last_modified=parsed.get("modified"),
        status=(
            schemas.FeedFetchStatus.NO_CHANGE
            if parsed.status == 304
            else schemas.FeedFetchStatus.GONE
            if parsed.status == 410
            else schemas.FeedFetchStatus.PERMANENT_REDIRECT
            if parsed.status == 301
            else schemas.FeedFetchStatus.TRY_LATER
            if parsed.status >= 500
            else schemas.FeedFetchStatus.GENERIC_ERROR
            if parsed.status >= 400
            else schemas.FeedFetchStatus.FETCHED
        ),
        items=[process_item(entry) for entry in parsed.get("entries", [])],
    )


def update_items(db: Session, feed: schemas.Feed, items: list[schemas.ItemFetched], now: datetime.datetime):
    existing_items = {
        item.item_id: item
        for item in db.execute(
            select(models.Item).where(
                models.Item.feed_id == feed.id,
                models.Item.item_id.in_(item.item_id for item in items),
            )
        ).scalars()
    }

    items_dict = {item.item_id: item for item in items}

    for item_id, item in items_dict.items():
        if item_id in existing_items:
            existing = existing_items[item_id]
            if item.updated is None or item.updated <= existing.updated:
                continue
            existing.title = item.title
            existing.link = item.link
            existing.author = item.author
            existing.summary = item.summary
            existing.content = item.content
            existing.updated = item.updated if item.updated is not None else now
            db.add(existing)
        else:
            item.updated = item.updated if item.updated is not None else now
            feed.items.append(
                models.Item(
                    **item.model_dump(),
                    first_seen=now,
                )
            )


def fetch_feed_by_id(
    db: Session, feed_id: int, force_fetch: bool = False
) -> schemas.Feed:
    feed: Optional[models.Feed] = db.query(models.Feed).get(feed_id)
    if feed is None:
        raise FeedNotFoundError()
    feed_for_fetch = schemas.FeedForFetch.from_orm(feed)
    feed_for_fetch.source = schemas.PublicUrl(
        feed.actual_source if feed.actual_source is not None else feed.source
    )
    fetched = fetch_feed(feed_for_fetch, force_fetch=force_fetch)

    now = datetime.datetime.now()
    feed.last_fetch = now
    
    if fetched.status == schemas.FeedFetchStatus.GONE:
        print("Gone!")
        feed.status = FeedStatus.GONE
    elif fetched.status == schemas.FeedFetchStatus.TRY_LATER:
        print("Later!")
        feed.status = FeedStatus.TRY_LATER
    elif fetched.status == schemas.FeedFetchStatus.GENERIC_ERROR:
        print("something odd?")
        feed.status = FeedStatus.FAILED
    elif not fetched.status.ok:
        raise NotImplementedError("Missing error handling")
    else:
        feed.status = FeedStatus.OK


    if not fetched.status.update:
        return schemas.Feed.from_orm(feed)

    if fetched.status.update:
        feed.etag = fetched.etag
        feed.last_modified = fetched.last_modified
        if fetched.status == schemas.FeedFetchStatus.PERMANENT_REDIRECT:
            feed.actual_source = str(fetched.source)

        update_items(db, feed, fetched.items, now)
    feed.status = FeedStatus.OK

    db.add(feed)
    db.commit()
    db.refresh(feed)
    return schemas.Feed.from_orm(feed)
