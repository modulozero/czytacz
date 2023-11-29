# Czytacz

An API RSS feed reader, implemented as a recruitment assignment.

## Design Decisions

Built from a single code base - to run different components, start different
scripts.

Stuck to FastAPI, which slowed me down, but I wanted to try it.

## To run

To try it out, just use docker-compose. Make sure you have Docker and 
docker-compose installed, then run:
```
$ docker-compose up
```

After a while, the API should be available at http://localhost:8000/docs.
Endpoints other than creating a user require HTTP basic authentication -
there is a button in the top right of the documentation page that lets you
set ip up, and try out all services interactively.

### Devcontainer

There's also a devcontainer - with more time, I'd get it synchronized with
the main Dockerfile. In VS Code it should be possible to just connect to it.
In two separate terminals, run:

```
$ poetry install
# Wait for stuff
$ poetry run czytacz api
```

```
$ poetry install
# Wait for stuff
$ poetry run celery -A czytacz.tasks worker --loglevel=INFO -B
```

The API will be at http://localhost:8000

## Notes

I'd probably go with [pip-tools](https://github.com/jazzband/pip-tools) if I
started from scratch, but I forgot I was going to investigate them when I
started this.

I haven't used SQLModel - easy integration is tempting, but it seems to rely
on older pydantic than I already had. I happen to quite like SQL Alchemy, so
I happily moved on.

Due to lack of time I didn't do any testing - but serialization and database
access could definitely benefit from it. 

## Ideas For Later
- Feeds with the same source should be only fetched once
- If the "updated" field is not present, I don't update the item. This may be 
  wrong.
- Feedparser is a fairly limited http clients. It would be best to switch to
  something else, like requests.
- I haven't really touched the async features of FastAPI. For some database
  queries that could be a big win.
  