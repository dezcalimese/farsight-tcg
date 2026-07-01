from typing import Literal

from pydantic import BaseModel, field_validator


class SignupRequest(BaseModel):
    contact: str
    channel: Literal["email", "sms"]
    cadence: Literal["daily", "weekly"] = "daily"

    @field_validator("contact")
    @classmethod
    def strip_contact(cls, v: str) -> str:
        return v.strip()


class ConfirmOtpRequest(BaseModel):
    contact: str
    code: str


class SignupResponse(BaseModel):
    status: str
    channel: str
    portfolio_token: str | None = None
