"""Manually run one alert-evaluation cycle. Useful for local testing."""

import asyncio
import logging

from app.jobs.alerts import evaluate_all_alerts


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    results = await evaluate_all_alerts()
    print(f"alert check results: {results}")


if __name__ == "__main__":
    asyncio.run(main())
