import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import ConfirmOtpRequest, SignupRequest, SignupResponse
from app.api.tokens import generate_confirm_token, generate_otp, generate_portfolio_token, generate_unsubscribe_token
from app.config import Settings, get_settings
from app.db.models import Subscriber
from app.db.session import get_session
from app.delivery.transactional import send_magic_link, send_otp_sms

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

_templates_dir = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(_templates_dir), autoescape=select_autoescape(["html"]))

_EMAIL_TOKEN_TTL = timedelta(minutes=30)
_OTP_TTL = timedelta(minutes=10)


def _render_message(message: str) -> HTMLResponse:
    html = _env.get_template("message.html.j2").render(message=message)
    return HTMLResponse(html)


@router.post("/signup", response_model=SignupResponse)
async def signup(
    body: SignupRequest,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> SignupResponse:
    if body.channel == "email":
        if "@" not in body.contact:
            raise HTTPException(422, "That doesn't look like a valid email address.")
        contact = body.contact.lower()
        lookup = select(Subscriber).where(Subscriber.email == contact)
    else:
        if not body.contact.startswith("+") or not body.contact[1:].isdigit():
            raise HTTPException(422, "Phone number must be in E.164 format, e.g. +15551234567.")
        contact = body.contact
        lookup = select(Subscriber).where(Subscriber.phone == contact)

    result = await session.execute(lookup)
    subscriber = result.scalar_one_or_none()

    if subscriber and subscriber.status == "active":
        subscriber.cadence = body.cadence
        await session.commit()
        return SignupResponse(status="already_active", channel=body.channel)

    now = datetime.now(timezone.utc)
    if body.channel == "email":
        token = generate_confirm_token()
        expires_at = now + _EMAIL_TOKEN_TTL
    else:
        token = generate_otp()
        expires_at = now + _OTP_TTL

    if subscriber is None:
        subscriber = Subscriber(
            email_enabled=body.channel == "email",
            sms_enabled=body.channel == "sms",
            cadence=body.cadence,
            status="pending_verification",
            unsubscribe_token=generate_unsubscribe_token(),
            portfolio_token=generate_portfolio_token(),
        )
        if body.channel == "email":
            subscriber.email = contact
        else:
            subscriber.phone = contact
        session.add(subscriber)
    else:
        subscriber.cadence = body.cadence
        subscriber.status = "pending_verification"

    subscriber.confirm_token = token
    subscriber.confirm_token_expires_at = expires_at
    await session.flush()

    if body.channel == "email":
        confirm_url = f"{settings.base_url}/api/confirm?token={token}"
        sent = await send_magic_link(settings, contact, confirm_url)
    else:
        sent = await send_otp_sms(settings, contact, token)

    if not sent:
        await session.rollback()
        raise HTTPException(502, "Couldn't send the confirmation message. Try again in a moment.")

    await session.commit()
    return SignupResponse(status="pending_verification", channel=body.channel)


@router.get("/confirm", response_class=HTMLResponse)
async def confirm(
    token: str,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> HTMLResponse:
    now = datetime.now(timezone.utc)
    result = await session.execute(select(Subscriber).where(Subscriber.confirm_token == token))
    subscriber = result.scalar_one_or_none()

    if subscriber is None or subscriber.confirm_token_expires_at is None or subscriber.confirm_token_expires_at < now:
        return _render_message("That confirmation link is invalid or has expired. Please sign up again.")

    subscriber.status = "active"
    subscriber.confirmed_at = now
    subscriber.confirm_token = None
    subscriber.confirm_token_expires_at = None
    await session.commit()

    channel_label = "email" if subscriber.email_enabled else "text"
    portfolio_url = f"{settings.frontend_origin}/portfolio?token={subscriber.portfolio_token}"
    return _render_message(
        f"You're in. Farsight digests will arrive by {channel_label} on a {subscriber.cadence} cadence. "
        f'<br><br>Want to track your own cards, set alerts, or change your preferences? '
        f'<a href="{portfolio_url}">Go to your portfolio</a>.'
    )


@router.post("/confirm-otp", response_model=SignupResponse)
async def confirm_otp(body: ConfirmOtpRequest, session: AsyncSession = Depends(get_session)) -> SignupResponse:
    now = datetime.now(timezone.utc)
    result = await session.execute(select(Subscriber).where(Subscriber.phone == body.contact))
    subscriber = result.scalar_one_or_none()

    if (
        subscriber is None
        or subscriber.confirm_token != body.code
        or subscriber.confirm_token_expires_at is None
        or subscriber.confirm_token_expires_at < now
    ):
        raise HTTPException(422, "That code is invalid or has expired.")

    subscriber.status = "active"
    subscriber.confirmed_at = now
    subscriber.confirm_token = None
    subscriber.confirm_token_expires_at = None
    await session.commit()

    return SignupResponse(status="active", channel="sms", portfolio_token=subscriber.portfolio_token)


@router.get("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe(token: str, session: AsyncSession = Depends(get_session)) -> HTMLResponse:
    result = await session.execute(select(Subscriber).where(Subscriber.unsubscribe_token == token))
    subscriber = result.scalar_one_or_none()

    if subscriber is None:
        return _render_message("That unsubscribe link is invalid.")

    subscriber.status = "unsubscribed"
    await session.commit()

    return _render_message("You're unsubscribed. You won't receive any more Farsight digests.")
