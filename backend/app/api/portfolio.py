import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_subscriber_by_portfolio_token
from app.db.models import Card, Holding, SealedProduct
from app.db.session import get_session
from app.pricing import get_latest_price

router = APIRouter(prefix="/api")


class CatalogItem(BaseModel):
    item_id: str
    item_type: Literal["card", "sealed_product"]
    name: str
    image_url: str | None


class HoldingIn(BaseModel):
    item_type: Literal["card", "sealed_product"]
    item_id: uuid.UUID
    quantity: int
    purchase_price: float
    purchase_date: datetime


class HoldingOut(BaseModel):
    id: str
    item_type: Literal["card", "sealed_product"]
    item_id: str
    item_name: str
    image_url: str | None
    quantity: int
    purchase_price: float
    purchase_date: datetime
    current_price: float | None
    cost_basis: float
    market_value: float | None
    pnl: float | None
    pnl_pct: float | None


class PortfolioOut(BaseModel):
    holdings: list[HoldingOut]
    total_cost: float
    total_value: float | None
    total_pnl: float | None


@router.get("/catalog/search", response_model=list[CatalogItem])
async def catalog_search(q: str, session: AsyncSession = Depends(get_session)) -> list[CatalogItem]:
    if len(q.strip()) < 2:
        return []
    like = f"%{q.strip()}%"
    cards = (
        await session.execute(select(Card).where(Card.name.ilike(like)).limit(10))
    ).scalars().all()
    products = (
        await session.execute(select(SealedProduct).where(SealedProduct.name.ilike(like)).limit(10))
    ).scalars().all()
    return [
        CatalogItem(item_id=str(c.id), item_type="card", name=c.name, image_url=c.image_url) for c in cards
    ] + [
        CatalogItem(item_id=str(p.id), item_type="sealed_product", name=p.name, image_url=p.image_url)
        for p in products
    ]


@router.get("/portfolio", response_model=PortfolioOut)
async def get_portfolio(token: str, session: AsyncSession = Depends(get_session)) -> PortfolioOut:
    subscriber = await get_subscriber_by_portfolio_token(session, token)
    result = await session.execute(
        select(Holding, Card.name, Card.image_url, SealedProduct.name, SealedProduct.image_url)
        .outerjoin(Card, Holding.card_id == Card.id)
        .outerjoin(SealedProduct, Holding.sealed_product_id == SealedProduct.id)
        .where(Holding.subscriber_id == subscriber.id)
        .order_by(Holding.created_at.desc())
    )

    holdings_out: list[HoldingOut] = []
    total_cost = 0.0
    total_value = 0.0
    any_missing_price = False

    for holding, card_name, card_image, sealed_name, sealed_image in result.all():
        if holding.card_id:
            item_type, item_name, image_url = "card", card_name, card_image
        else:
            item_type, item_name, image_url = "sealed_product", sealed_name, sealed_image

        current_price = await get_latest_price(session, item_type, holding.card_id or holding.sealed_product_id)
        purchase_price = float(holding.purchase_price)
        cost_basis = purchase_price * holding.quantity
        total_cost += cost_basis

        market_value = current_price * holding.quantity if current_price is not None else None
        pnl = (market_value - cost_basis) if market_value is not None else None
        pnl_pct = (pnl / cost_basis * 100) if pnl is not None and cost_basis > 0 else None

        if market_value is not None:
            total_value += market_value
        else:
            any_missing_price = True

        holdings_out.append(
            HoldingOut(
                id=str(holding.id),
                item_type=item_type,
                item_id=str(holding.card_id or holding.sealed_product_id),
                item_name=item_name or "Unknown item",
                image_url=image_url,
                quantity=holding.quantity,
                purchase_price=purchase_price,
                purchase_date=holding.purchase_date,
                current_price=current_price,
                cost_basis=round(cost_basis, 2),
                market_value=round(market_value, 2) if market_value is not None else None,
                pnl=round(pnl, 2) if pnl is not None else None,
                pnl_pct=round(pnl_pct, 2) if pnl_pct is not None else None,
            )
        )

    return PortfolioOut(
        holdings=holdings_out,
        total_cost=round(total_cost, 2),
        total_value=None if (any_missing_price and total_value == 0) else round(total_value, 2),
        total_pnl=None if (any_missing_price and total_value == 0) else round(total_value - total_cost, 2),
    )


@router.post("/portfolio/holdings", response_model=HoldingOut)
async def add_holding(
    token: str, body: HoldingIn, session: AsyncSession = Depends(get_session)
) -> HoldingOut:
    subscriber = await get_subscriber_by_portfolio_token(session, token)

    if body.item_type == "card":
        item = (await session.execute(select(Card).where(Card.id == body.item_id))).scalar_one_or_none()
    else:
        item = (
            await session.execute(select(SealedProduct).where(SealedProduct.id == body.item_id))
        ).scalar_one_or_none()
    if item is None:
        raise HTTPException(404, "That card or product doesn't exist.")

    holding = Holding(
        subscriber_id=subscriber.id,
        card_id=body.item_id if body.item_type == "card" else None,
        sealed_product_id=body.item_id if body.item_type == "sealed_product" else None,
        quantity=body.quantity,
        purchase_price=body.purchase_price,
        purchase_date=body.purchase_date,
    )
    session.add(holding)
    await session.commit()

    current_price = await get_latest_price(session, body.item_type, body.item_id)
    cost_basis = body.purchase_price * body.quantity
    market_value = current_price * body.quantity if current_price is not None else None
    pnl = (market_value - cost_basis) if market_value is not None else None

    return HoldingOut(
        id=str(holding.id),
        item_type=body.item_type,
        item_id=str(body.item_id),
        item_name=item.name,
        image_url=item.image_url,
        quantity=body.quantity,
        purchase_price=body.purchase_price,
        purchase_date=body.purchase_date,
        current_price=current_price,
        cost_basis=round(cost_basis, 2),
        market_value=round(market_value, 2) if market_value is not None else None,
        pnl=round(pnl, 2) if pnl is not None else None,
        pnl_pct=round(pnl / cost_basis * 100, 2) if pnl is not None and cost_basis > 0 else None,
    )


@router.delete("/portfolio/holdings/{holding_id}")
async def delete_holding(
    holding_id: uuid.UUID, token: str, session: AsyncSession = Depends(get_session)
) -> dict[str, bool]:
    subscriber = await get_subscriber_by_portfolio_token(session, token)
    result = await session.execute(
        select(Holding).where(Holding.id == holding_id, Holding.subscriber_id == subscriber.id)
    )
    holding = result.scalar_one_or_none()
    if holding is None:
        raise HTTPException(404, "Holding not found.")
    await session.delete(holding)
    await session.commit()
    return {"deleted": True}
