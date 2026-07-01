"""Phase 1: manually trigger digest generation and print both renders for review.

Usage: python -m scripts.generate_digest [period_days] [--html-out path]
"""

import asyncio
import sys

from app.db.session import async_session_factory
from app.digest.generator import generate_digest
from app.digest.render_html import render_html
from app.digest.render_text import render_text


async def main() -> None:
    period_days = 7
    html_out = None
    args = sys.argv[1:]
    if args and args[0].isdigit():
        period_days = int(args[0])
    if "--html-out" in args:
        html_out = args[args.index("--html-out") + 1]

    async with async_session_factory() as session:
        digest = await generate_digest(session, period_days=period_days)

    print("=" * 60)
    print("PLAIN TEXT (SMS/email fallback)")
    print("=" * 60)
    print(render_text(digest))

    html = render_html(digest)
    if html_out:
        with open(html_out, "w") as f:
            f.write(html)
        print(f"HTML written to {html_out}")
    else:
        print("=" * 60)
        print("HTML length:", len(html), "chars — pass --html-out <path> to save and open it")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
