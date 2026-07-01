from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

router = APIRouter()

_templates_dir = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(_templates_dir), autoescape=select_autoescape(["html"]))


@router.get("/", response_class=HTMLResponse)
async def landing() -> HTMLResponse:
    return HTMLResponse(_env.get_template("landing.html.j2").render())
