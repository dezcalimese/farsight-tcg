from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_subscriber_by_portfolio_token
from app.api.tokens import generate_confirm_token, generate_otp
from app.config import Settings, get_settings
from app.db.models import Subscriber
from app.db.session import get_session
from app.delivery.transactional import send_magic_link, send_otp_sms

router = APIRouter(prefix="/api")

_templates_dir = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(_templates_dir), autoescape=select_autoescape(["html"]))

_EMAIL_TOKEN_TTL = timedelta(minutes=30)
_OTP_TTL = timedelta(minutes=10)


def _render_message(message: str) -> HTMLResponse:
    return HTMLResponse(_env.get_template("message.html.j2").render(message=message))


class SettingsOut(BaseModel):
    email: str | None
    phone: str | None
    email_enabled: bool
    sms_enabled: bool
    cadence: Literal["daily", "weekly"]
    mute_movers: bool
    mute_restocks: bool
    mute_news: bool
    pending_channel: Literal["email", "sms"] | None


class SettingsPatch(BaseModel):
    cadence: Literal["daily", "weekly"] | None = None
    mute_movers: bool | None = None
    mute_restocks: bool | None = None
    mute_news: bool | None = None


class ChannelTogglePatch(BaseModel):
    email_enabled: bool | None = None
    sms_enabled: bool | None = None


class AddChannelIn(BaseModel):
    channel: Literal["email", "sms"]
    contact: str


class ConfirmSmsChannelIn(BaseModel):
    code: str


def _serialize(subscriber: Subscriber) -> SettingsOut:
    pending_channel = None
    if subscriber.pending_contact:
        pending_channel = "email" if "@" in subscriber.pending_contact else "sms"
    return SettingsOut(
        email=subscriber.email,
        phone=subscriber.phone,
        email_enabled=subscriber.email_enabled,
        sms_enabled=subscriber.sms_enabled,
        cadence=subscriber.cadence,
        mute_movers=subscriber.mute_movers,
        mute_restocks=subscriber.mute_restocks,
        mute_news=subscriber.mute_news,
        pending_channel=pending_channel,
    )


@router.get("/settings", response_model=SettingsOut)
async def get_settings_view(token: str, session: AsyncSession = Depends(get_session)) -> SettingsOut:
    subscriber = await get_subscriber_by_portfolio_token(session, token)
    return _serialize(subscriber)


@router.patch("/settings", response_model=SettingsOut)
async def update_settings(
    token: str, body: SettingsPatch, session: AsyncSession = Depends(get_session)
) -> SettingsOut:
    subscriber = await get_subscriber_by_portfolio_token(session, token)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(subscriber, field, value)
    await session.commit()
    return _serialize(subscriber)


@router.patch("/settings/channels", response_model=SettingsOut)
async def toggle_channels(
    token: str, body: ChannelTogglePatch, session: AsyncSession = Depends(get_session)
) -> SettingsOut:
    subscriber = await get_subscriber_by_portfolio_token(session, token)

    new_email_enabled = body.email_enabled if body.email_enabled is not None else subscriber.email_enabled
    new_sms_enabled = body.sms_enabled if body.sms_enabled is not None else subscriber.sms_enabled

    if new_email_enabled and subscriber.email is None:
        raise HTTPException(422, "Add and verify an email address first.")
    if new_sms_enabled and subscriber.phone is None:
        raise HTTPException(422, "Add and verify a phone number first.")
    if not new_email_enabled and not new_sms_enabled:
        raise HTTPException(422, "You need at least one enabled delivery channel.")

    subscriber.email_enabled = new_email_enabled
    subscriber.sms_enabled = new_sms_enabled
    await session.commit()
    return _serialize(subscriber)


@router.post("/settings/channels/add", response_model=SettingsOut)
async def add_channel(
    token: str,
    body: AddChannelIn,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> SettingsOut:
    subscriber = await get_subscriber_by_portfolio_token(session, token)

    if body.channel == "email":
        if "@" not in body.contact:
            raise HTTPException(422, "That doesn't look like a valid email address.")
        contact = body.contact.lower()
        if subscriber.email == contact:
            raise HTTPException(422, "That's already your email address.")
        existing = await session.execute(select(Subscriber).where(Subscriber.email == contact))
    else:
        if not body.contact.startswith("+") or not body.contact[1:].isdigit():
            raise HTTPException(422, "Phone number must be in E.164 format, e.g. +15551234567.")
        contact = body.contact
        if subscriber.phone == contact:
            raise HTTPException(422, "That's already your phone number.")
        existing = await session.execute(select(Subscriber).where(Subscriber.phone == contact))

    if existing.scalar_one_or_none() is not None:
        raise HTTPException(422, "That contact is already in use by another account.")

    now = datetime.now(timezone.utc)
    if body.channel == "email":
        token_value = generate_confirm_token()
        expires_at = now + _EMAIL_TOKEN_TTL
    else:
        token_value = generate_otp()
        expires_at = now + _OTP_TTL

    subscriber.pending_contact = contact
    subscriber.confirm_token = token_value
    subscriber.confirm_token_expires_at = expires_at
    await session.flush()

    if body.channel == "email":
        confirm_url = f"{settings.base_url}/api/settings/channels/confirm-email?token={token_value}"
        sent = await send_magic_link(settings, contact, confirm_url)
    else:
        sent = await send_otp_sms(settings, contact, token_value)

    if not sent:
        await session.rollback()
        raise HTTPException(502, "Couldn't send the confirmation message. Try again in a moment.")

    await session.commit()
    return _serialize(subscriber)


@router.get("/settings/channels/confirm-email", response_class=HTMLResponse)
async def confirm_email_channel(token: str, session: AsyncSession = Depends(get_session)) -> HTMLResponse:
    now = datetime.now(timezone.utc)
    result = await session.execute(select(Subscriber).where(Subscriber.confirm_token == token))
    subscriber = result.scalar_one_or_none()

    if (
        subscriber is None
        or subscriber.pending_contact is None
        or subscriber.confirm_token_expires_at is None
        or subscriber.confirm_token_expires_at < now
    ):
        return _render_message("That confirmation link is invalid or has expired.")

    subscriber.email = subscriber.pending_contact
    subscriber.email_enabled = True
    subscriber.pending_contact = None
    subscriber.confirm_token = None
    subscriber.confirm_token_expires_at = None
    await session.commit()

    return _render_message("Email added — you'll now get digests there too. You can close this tab.")


@router.post("/settings/channels/confirm-sms", response_model=SettingsOut)
async def confirm_sms_channel(
    token: str, body: ConfirmSmsChannelIn, session: AsyncSession = Depends(get_session)
) -> SettingsOut:
    subscriber = await get_subscriber_by_portfolio_token(session, token)
    now = datetime.now(timezone.utc)

    if (
        subscriber.pending_contact is None
        or subscriber.confirm_token != body.code
        or subscriber.confirm_token_expires_at is None
        or subscriber.confirm_token_expires_at < now
    ):
        raise HTTPException(422, "That code is invalid or has expired.")

    subscriber.phone = subscriber.pending_contact
    subscriber.sms_enabled = True
    subscriber.pending_contact = None
    subscriber.confirm_token = None
    subscriber.confirm_token_expires_at = None
    await session.commit()
    return _serialize(subscriber)


@router.delete("/account")
async def delete_account(token: str, session: AsyncSession = Depends(get_session)) -> dict[str, bool]:
    subscriber = await get_subscriber_by_portfolio_token(session, token)
    await session.delete(subscriber)
    await session.commit()
    return {"deleted": True}
