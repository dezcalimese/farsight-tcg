"""Phase 2: manually trigger a real digest send through all configured channels."""

import asyncio
import logging

from app.jobs.send_digest import send_digest_job


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    results = await send_digest_job()
    print(f"send results: {results}")


if __name__ == "__main__":
    asyncio.run(main())
