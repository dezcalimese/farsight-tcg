import time

import httpx

from app.config import Settings
from app.sources.base import PricePoint, PriceSource

POKEMON_CATEGORY_ID = 3
SEALED_KEYWORDS = (
    "booster box",
    "booster bundle",
    "elite trainer box",
    "etb",
    "bundle",
    "tin",
    "collection",
    "blister",
    "build & battle",
    "premium",
    "case",
)


def _looks_sealed(product_name: str) -> bool:
    lowered = product_name.lower()
    return any(keyword in lowered for keyword in SEALED_KEYWORDS)


class TCGPlayerPriceSource(PriceSource):
    """Real TCGPlayer REST client. Requires TCGPLAYER_CLIENT_ID/SECRET.

    Discovers recently-updated Pokemon products from the public catalog and
    pulls current market pricing for them. No local product catalog required
    to run — matching prices to our own Card/SealedProduct rows happens
    downstream in the ingestion job.
    """

    name = "tcgplayer"
    BASE_URL = "https://api.tcgplayer.com"

    def __init__(self, settings: Settings, product_limit: int = 50) -> None:
        self._client_id = settings.tcgplayer_client_id
        self._client_secret = settings.tcgplayer_client_secret
        self._product_limit = product_limit
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    async def _get_token(self, client: httpx.AsyncClient) -> str:
        if self._token and time.time() < self._token_expires_at:
            return self._token
        resp = await client.post(
            f"{self.BASE_URL}/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )
        resp.raise_for_status()
        payload = resp.json()
        self._token = payload["access_token"]
        self._token_expires_at = time.time() + payload.get("expires_in", 1200) - 60
        return self._token

    async def _fetch_recent_product_ids(self, client: httpx.AsyncClient, token: str) -> list[dict]:
        resp = await client.get(
            f"{self.BASE_URL}/catalog/products",
            params={
                "categoryId": POKEMON_CATEGORY_ID,
                "limit": self._product_limit,
                "sortOrder": "releaseDate",
                "sortDesc": "true",
                "getExtendedFields": "false",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return resp.json().get("results", [])

    async def _fetch_pricing(self, client: httpx.AsyncClient, token: str, product_ids: list[int]) -> list[dict]:
        if not product_ids:
            return []
        ids_param = ",".join(str(pid) for pid in product_ids)
        resp = await client.get(
            f"{self.BASE_URL}/pricing/product/{ids_param}",
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return resp.json().get("results", [])

    async def fetch_prices(self) -> list[PricePoint]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            token = await self._get_token(client)
            products = await self._fetch_recent_product_ids(client, token)
            product_by_id = {p["productId"]: p for p in products}
            pricing_rows = await self._fetch_pricing(client, token, list(product_by_id.keys()))

            # TCGPlayer returns one row per sub-type (Normal/Holofoil/1st Edition, etc).
            # Collapse to one PricePoint per product, preferring "Normal"/"Holofoil".
            best_row_by_product: dict[int, dict] = {}
            for row in pricing_rows:
                pid = row["productId"]
                current = best_row_by_product.get(pid)
                if current is None or row.get("subTypeName") in ("Normal", "Holofoil"):
                    best_row_by_product[pid] = row

            points: list[PricePoint] = []
            for pid, row in best_row_by_product.items():
                product = product_by_id.get(pid, {})
                name = product.get("name", f"Unknown Product {pid}")
                points.append(
                    PricePoint(
                        item_name=name,
                        item_type="sealed_product" if _looks_sealed(name) else "card",
                        tcgplayer_product_id=str(pid),
                        set_name=product.get("groupId") and str(product.get("groupId")),
                        price_low=row.get("lowPrice"),
                        price_mid=row.get("midPrice"),
                        price_high=row.get("highPrice"),
                        market_price=row.get("marketPrice"),
                        image_url=product.get("imageUrl"),
                    )
                )
            return points
