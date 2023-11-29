import typer

from czytacz.fetcher import fetch_feed_by_id

app = typer.Typer()


@app.command()
def api(reload: bool = True, port: int = 8000):
    import uvicorn

    uvicorn.run("czytacz.api:app", reload=reload, port=port, host="0.0.0.0")


@app.command()
def fetch(feed_id: int, force_fetch: bool = False):
    from czytacz.dependencies import get_db_cli

    with get_db_cli() as db:
        fetch_feed_by_id(db, feed_id, force_fetch=force_fetch)


if __name__ == "__main__":
    app()
