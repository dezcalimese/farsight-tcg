import logging

from fastapi import FastAPI

from app.api import pages, signup
from app.config import get_settings

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Farsight", version="0.1.0")
app.include_router(pages.router)
app.include_router(signup.router)


@app.get("/health")
async def health() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "env": settings.env}
