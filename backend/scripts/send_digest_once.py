"""Manually trigger a real digest send to every active subscriber on a cadence.

Usage: python -m scripts.send_digest_once [daily|weekly]
"""

import asyncio
import logging
import sys

from app.jobs.send_digest import send_digest_for_cadence


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    cadence = sys.argv[1] if len(sys.argv) > 1 else "daily"
    results = await send_digest_for_cadence(cadence, include_discord=(cadence == "daily"))
    print(f"send results ({cadence}): {results}")


if __name__ == "__main__":
    asyncio.run(main())
