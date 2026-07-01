from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.digest.schemas import DigestData

_TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR), autoescape=select_autoescape(["html"]))

_PERIOD_LABEL = {1: "Today", 7: "This Week"}


def render_html(
    digest: DigestData,
    unsubscribe_url: str | None = None,
    portfolio_url: str | None = None,
    personal_line: str | None = None,
) -> str:
    template = _env.get_template("digest.html.j2")
    return template.render(
        period_label=_PERIOD_LABEL.get(digest.period_days, f"Last {digest.period_days} Days"),
        generated_at=digest.generated_at.strftime("%b %d, %Y"),
        is_empty=digest.is_empty,
        trending_cards=digest.trending_cards,
        top_movers=digest.top_movers,
        restocks=digest.restocks,
        news=digest.news,
        unsubscribe_url=unsubscribe_url,
        portfolio_url=portfolio_url,
        personal_line=personal_line,
    )
