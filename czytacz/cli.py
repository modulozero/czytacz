from contextlib import contextmanager

import typer

app = typer.Typer()


@app.command()
def api(reload: bool = True, port: int = 8000):
    import uvicorn

    uvicorn.run("czytacz.api:app", reload=reload, port=port)


@app.command()
def fetch(feed_id: int, force_fetch: bool = False):
    from czytacz.database import get_db
    from czytacz.fetcher import fetch_feed_by_id

    fetch_feed_by_id(next(get_db()), feed_id, force_fetch=force_fetch)


if __name__ == "__main__":
    app()
