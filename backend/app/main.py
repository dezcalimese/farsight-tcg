import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import alerts, dashboard, pages, portfolio, settings as settings_api, signup
from app.config import get_settings

logging.basicConfig(level=logging.INFO)

settings = get_settings()

app = FastAPI(title="Farsight", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)
app.include_router(pages.router)
app.include_router(signup.router)
app.include_router(dashboard.router)
app.include_router(portfolio.router)
app.include_router(alerts.router)
app.include_router(settings_api.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.env}
