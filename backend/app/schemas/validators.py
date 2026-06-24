"""Reusable field validators and annotated types for request schemas.

These provide format-level validation (email, password strength, name, phone)
so malformed input is rejected with a 422 before any side effects — e.g. before
an OTP email is queued for an address that could never receive it.
"""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import AfterValidator

# Practical email format: non-empty local part, single @, a domain with at
# least one dot and an alphabetic TLD of 2+ chars. Rejects the malformed input
# we care about ("asdf", "foo@", "foo@bar") while still accepting internal/dev
# domains (e.g. "name@host.local") that a strict RFC deliverability check bans.
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")

# A digit-led international-ish number: optional leading +, then 7–20 chars of
# digits, spaces, and common separators. Deliberately permissive about format
# while still rejecting obvious junk ("abc", "123").
_PHONE_RE = re.compile(r"^\+?[0-9][0-9\s().-]{6,19}$")

_HAS_LETTER = re.compile(r"[A-Za-z]")
_HAS_DIGIT = re.compile(r"\d")


def _check_email(value: str) -> str:
    cleaned = value.strip()
    if not _EMAIL_RE.match(cleaned):
        raise ValueError("Enter a valid email address")
    return cleaned


def _check_password(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not _HAS_LETTER.search(value):
        raise ValueError("Password must contain at least one letter")
    if not _HAS_DIGIT.search(value):
        raise ValueError("Password must contain at least one number")
    return value


def _check_name(value: str) -> str:
    cleaned = " ".join(value.split())
    if len(cleaned) < 2:
        raise ValueError("Name must be at least 2 characters long")
    return cleaned


def _check_required_phone(value: str) -> str:
    cleaned = value.strip()
    if not _PHONE_RE.match(cleaned):
        raise ValueError("Enter a valid phone number")
    return cleaned


def _check_phone(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return _check_required_phone(cleaned)


def _check_optional_password(value: str | None) -> str | None:
    if value is None:
        return None
    return _check_password(value)


def _check_optional_name(value: str | None) -> str | None:
    if value is None:
        return None
    return _check_name(value)


# Annotated types — attach to fields so the same rules are reused everywhere.
Email = Annotated[str, AfterValidator(_check_email)]
Password = Annotated[str, AfterValidator(_check_password)]
PersonName = Annotated[str, AfterValidator(_check_name)]
Phone = Annotated[str, AfterValidator(_check_required_phone)]
OptionalPhone = Annotated[str | None, AfterValidator(_check_phone)]
OptionalPassword = Annotated[str | None, AfterValidator(_check_optional_password)]
OptionalPersonName = Annotated[str | None, AfterValidator(_check_optional_name)]
