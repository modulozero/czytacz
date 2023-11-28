import datetime
from typing import Any, Optional

import feedparser
from sqlalchemy import select
from sqlalchemy.orm import Session

from czytacz import models, schemas


class FeedNotFoundError(Exception):
    pass


def process_item(feed_item: Any) -> schemas.ItemFetched:
    published_parsed = feed_item.get("published_parsed")
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
        parsed = feedparser.parse(feed.source)
    else:
        parsed = feedparser.parse(
            feed.source, etag=feed.etag, modified=feed.last_modified
        )

    if parsed.status == 304:
        return schemas.FeedFetchResult(
            source=feed.source,
            status=schemas.FeedFetchStatus.NO_CHANGE,
            etag=feed.etag,
            last_modified=feed.last_modified,
            items=[],
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
            else schemas.FeedFetchStatus.GENERIC_ERROR
            if parsed.status >= 400
            else schemas.FeedFetchStatus.FETCHED
        ),
        items=[process_item(entry) for entry in parsed.get("entries", [])],
    )


def fetch_feed_by_id(
    db: Session, feed_id: int, force_fetch: bool = False
) -> schemas.Feed:
    feed: Optional[models.Feed] = db.query(models.Feed).get(feed_id)
    if feed is None:
        raise FeedNotFoundError()
    feed_for_fetch = schemas.FeedForFetch.from_orm(feed)
    feed_for_fetch.source = (
        feed.actual_source if feed.actual_source is not None else feed.source
    )
    fetched = fetch_feed(feed_for_fetch, force_fetch=force_fetch)

    if not fetched.status.ok:
        raise NotImplementedError("Error handling? I'm no coward!")
    if not fetched.status.update:
        return schemas.Feed.from_orm(feed)

    if fetched.status.update:
        now = datetime.datetime.now()

        feed.etag = fetched.etag
        feed.last_modified = fetched.last_modified
        if fetched.status == schemas.FeedFetchStatus.PERMANENT_REDIRECT:
            feed.actual_source = fetched.source

        skip_item_ids = (
            db.execute(
                select(models.Item.item_id).where(
                    models.Item.feed_id == feed_id,
                    models.Item.item_id.in_(item.item_id for item in fetched.items),
                )
            )
            .scalars()
            .all()
        )

        for item in fetched.items:
            if item.item_id not in skip_item_ids:
                feed.items.append(models.Item(**item.model_dump(), first_seen=now))

    db.add(feed)
    db.commit()
    db.refresh(feed)
    return schemas.Feed.from_orm(feed)
