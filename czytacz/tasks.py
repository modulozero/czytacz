import datetime

from celery import Celery
from sqlalchemy import select, update, or_, and_

from czytacz import models, FeedStatus, fetcher
from czytacz.dependencies import get_db_cli, get_settings

settings = get_settings()
app = Celery("tasks", broker=str(settings.RABBITMQ_URI))


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        datetime.timedelta(minutes=5), queue_feeds, name="queue-feeds"
    )


RETRY_MAP = {
    0: 120,
    1: 300,
    2: 480,
}


@app.task(max_retries=None, rate_limit="100/m")
def fetch_feed(feed_id: int, force_fetch=False):
    with get_db_cli() as db:
        feed = fetcher.fetch_feed_by_id(db, feed_id)

    # I would actually use the built-in exponential back-off mechanism, but
    # I'm following the specification. I'm keeping the jitter enabled, though.
    if feed.status == FeedStatus.TRY_LATER:
        countdown = RETRY_MAP.get(fetch_feed.request.retries)
        if countdown is None:
            db.execute(
                update(models.Feed)
                .where(models.Feed.id == feed.id)
                .values(status=FeedStatus.FAILED)
            )
            db.commit()
        else:
            raise fetch_feed.retry(countdown=countdown)


@app.task()
def queue_feeds():
    now = datetime.datetime.now()
    fetch_since = now - datetime.timedelta(minutes=5)
    with get_db_cli() as db:
        feed_ids = (
            db.execute(
                select(models.Feed.id)
                .where(
                    and_(
                        or_(
                            models.Feed.last_fetch < fetch_since,
                            models.Feed.last_fetch.is_(None),
                        ),
                        or_(
                            models.Feed.status.in_ == FeedStatus.OK,
                            models.Feed.status.is_(None),
                        ),
                    )
                )
                .with_for_update()
            )
            .scalars()
            .all()
        )
        db.execute(
            update(models.Feed)
            .where(models.Feed.id.in_(feed_ids))
            .values(status=FeedStatus.FETCHING)
        )
        db.commit()
    fetch_feed.chunks(feed_ids, 10).delay()
