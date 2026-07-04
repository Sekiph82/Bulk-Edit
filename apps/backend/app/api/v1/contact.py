"""Public contact form endpoint — no auth required, rate limited."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, field_validator

from app.core.config import settings
from app.core.rate_limit import contact_rate_limit
from app.services.email import send_contact_notification_email

router = APIRouter(prefix="/contact", tags=["contact"])

_MAX_NAME_LEN = 200
_MAX_SUBJECT_LEN = 200
_MAX_MESSAGE_LEN = 5000


class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

    @field_validator("name")
    @classmethod
    def name_valid(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name is required")
        if len(v) > _MAX_NAME_LEN:
            raise ValueError(f"Name must be {_MAX_NAME_LEN} characters or fewer")
        return v

    @field_validator("subject")
    @classmethod
    def subject_valid(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Subject is required")
        if len(v) > _MAX_SUBJECT_LEN:
            raise ValueError(f"Subject must be {_MAX_SUBJECT_LEN} characters or fewer")
        return v

    @field_validator("message")
    @classmethod
    def message_valid(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Message is required")
        if len(v) > _MAX_MESSAGE_LEN:
            raise ValueError(f"Message must be {_MAX_MESSAGE_LEN} characters or fewer")
        return v


class ContactResponse(BaseModel):
    delivered: bool
    message: str


@router.post("", response_model=ContactResponse)
async def submit_contact_form(
    data: ContactRequest,
    _rl: None = Depends(contact_rate_limit),
):
    # Message contents are intentionally never logged — only send_email()'s
    # own safe logging (recipient domain + subject) touches this data.
    result = send_contact_notification_email(data.name, data.email, data.subject, data.message)

    if result.sent:
        return ContactResponse(
            delivered=True,
            message="Thanks for reaching out — we'll get back to you within one business day.",
        )

    return ContactResponse(
        delivered=False,
        message=(
            f"Email delivery isn't configured on this environment yet. "
            f"Please email us directly at {settings.SUPPORT_EMAIL} instead."
        ),
    )
