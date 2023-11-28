# Czytacz

An API RSS feed reader, implemented as a recruitment assignment.

## Design Decisions

Built from a single code base - to run different components, start different
scripts.

No RabbitMQ/Celery - they're actually pretty good choices, but I decided to
keep deployment units quite minimal. This creates extra cost for implementation
of the service worker, but I'm okay with that.

## To run

For now, no "production" docker container - later I'll add a "production"
`docker-compose` file.

```
$ poetry install
# Wait for stuff
$ poetry run czytacz api
```

## Notes

I'd probably go with [pip-tools](https://github.com/jazzband/pip-tools) if I
started from scratch, but I forgot I was going to investigate them when I
started this.

I haven't used SQLModel - easy integration is tempting, but it seems to rely
on older pydantic than I already had. I happen to quite like SQL Alchemy, so
I happily moved on.

## Ideas For Later
- Feeds with the same user ID