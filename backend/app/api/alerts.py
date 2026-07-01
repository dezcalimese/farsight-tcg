import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_subscriber_by_portfolio_token
from app.db.models import AlertRule, Card, SealedProduct
from app.db.session import get_session

router = APIRouter(prefix="/api")

RuleType = Literal["price_above", "price_below", "pct_move", "restock"]


class AlertRuleIn(BaseModel):
    rule_type: RuleType
    item_type: Literal["card", "sealed_product"] | None = None
    item_id: uuid.UUID | None = None
    watch_text: str | None = None
    threshold: float | None = None
    window_hours: int = 24

    @model_validator(mode="after")
    def _validate_shape(self) -> "AlertRuleIn":
        if self.rule_type == "restock":
            if not self.watch_text or not self.watch_text.strip():
                raise ValueError("restock rules need watch_text (the product name to watch for).")
        else:
            if self.item_type is None or self.item_id is None:
                raise ValueError(f"{self.rule_type} rules need item_type and item_id.")
            if self.threshold is None:
                raise ValueError(f"{self.rule_type} rules need a threshold.")
        return self


class AlertRuleOut(BaseModel):
    id: str
    rule_type: RuleType
    item_type: Literal["card", "sealed_product"] | None
    item_id: str | None
    item_name: str | None
    watch_text: str | None
    threshold: float | None
    window_hours: int
    last_triggered_at: str | None


def _serialize(rule: AlertRule, item_name: str | None) -> AlertRuleOut:
    item_type = "card" if rule.card_id else ("sealed_product" if rule.sealed_product_id else None)
    item_id = rule.card_id or rule.sealed_product_id
    return AlertRuleOut(
        id=str(rule.id),
        rule_type=rule.rule_type,
        item_type=item_type,
        item_id=str(item_id) if item_id else None,
        item_name=item_name,
        watch_text=rule.watch_text,
        threshold=float(rule.threshold) if rule.threshold is not None else None,
        window_hours=rule.window_hours,
        last_triggered_at=rule.last_triggered_at.isoformat() if rule.last_triggered_at else None,
    )


@router.get("/alerts", response_model=list[AlertRuleOut])
async def list_alerts(token: str, session: AsyncSession = Depends(get_session)) -> list[AlertRuleOut]:
    subscriber = await get_subscriber_by_portfolio_token(session, token)
    result = await session.execute(
        select(AlertRule, Card.name, SealedProduct.name)
        .outerjoin(Card, AlertRule.card_id == Card.id)
        .outerjoin(SealedProduct, AlertRule.sealed_product_id == SealedProduct.id)
        .where(AlertRule.subscriber_id == subscriber.id)
        .order_by(AlertRule.created_at.desc())
    )
    return [_serialize(rule, card_name or sealed_name) for rule, card_name, sealed_name in result.all()]


@router.post("/alerts", response_model=AlertRuleOut)
async def create_alert(
    token: str, body: AlertRuleIn, session: AsyncSession = Depends(get_session)
) -> AlertRuleOut:
    subscriber = await get_subscriber_by_portfolio_token(session, token)

    item_name: str | None = None
    card_id = sealed_product_id = None
    if body.rule_type != "restock":
        if body.item_type == "card":
            item = (await session.execute(select(Card).where(Card.id == body.item_id))).scalar_one_or_none()
            card_id = body.item_id
        else:
            item = (
                await session.execute(select(SealedProduct).where(SealedProduct.id == body.item_id))
            ).scalar_one_or_none()
            sealed_product_id = body.item_id
        if item is None:
            raise HTTPException(404, "That card or product doesn't exist.")
        item_name = item.name

    rule = AlertRule(
        subscriber_id=subscriber.id,
        rule_type=body.rule_type,
        card_id=card_id,
        sealed_product_id=sealed_product_id,
        watch_text=body.watch_text.strip() if body.watch_text else None,
        threshold=body.threshold,
        window_hours=body.window_hours,
    )
    session.add(rule)
    await session.commit()
    return _serialize(rule, item_name)


@router.delete("/alerts/{rule_id}")
async def delete_alert(
    rule_id: uuid.UUID, token: str, session: AsyncSession = Depends(get_session)
) -> dict[str, bool]:
    subscriber = await get_subscriber_by_portfolio_token(session, token)
    result = await session.execute(
        select(AlertRule).where(AlertRule.id == rule_id, AlertRule.subscriber_id == subscriber.id)
    )
    rule = result.scalar_one_or_none()
    if rule is None:
        raise HTTPException(404, "Alert rule not found.")
    await session.delete(rule)
    await session.commit()
    return {"deleted": True}
