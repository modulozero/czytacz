from fastapi import FastAPI

from czytacz.api.routers import authentication, feeds

app = FastAPI()
app.include_router(authentication.router)
app.include_router(feeds.router)
