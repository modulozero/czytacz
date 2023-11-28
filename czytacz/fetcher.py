import datetime
from typing import Any, Optional

import feedparser
from sqlalchemy import exists
from sqlalchemy.orm import Session

from czytacz import models, schemas


class FeedNotFoundError(Exception):
    pass


def process_item(feed_item: Any) -> schemas.ItemCreate:
    published_parsed = feed_item.get("published_parsed")
    item = schemas.ItemCreate(
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
        content=[],
    )

    for feed_content in feed_item.get("content", []):
        item_content = schemas.ItemContent(
            content_type=feed_content.type,
            value=feed_content.value,
        )
        item.content.append(item_content)

    return item


def fetch_feed_by_id(
    db: Session, feed_id: int, force_fetch: bool = False
) -> schemas.Feed:
    feed: Optional[models.Feed] = db.query(models.Feed).get(feed_id)
    if feed is None:
        raise FeedNotFoundError()
    source = feed.actual_source if feed.actual_source is not None else feed.source
    if force_fetch:
        parsed = feedparser.parse(source)
    else:
        parsed = feedparser.parse(source, etag=feed.etag, modified=feed.last_modified)

    if parsed.status == 301:
        feed.actual_source = parsed.href
    elif parsed.status == 304:
        return schemas.Feed.from_orm(feed)

    feed.etag = parsed.get("etag")
    feed.last_modified = parsed.get("modified")
    now = datetime.datetime.now()

    for entry in parsed.entries:
        if db.query(
            exists().where(
                models.Item.feed_id == feed_id, models.Item.item_id == entry.id
            )
        ).scalar():
            # We already had this.
            # In the future it might make sense to update the item
            continue
        item = process_item(entry)
        db_item = models.Item(**item.model_dump(), feed_id=feed.id, first_seen=now)
        feed.items.append(db_item)

    db.add(feed)
    db.commit()
    db.refresh(feed)
    return schemas.Feed.from_orm(feed)
