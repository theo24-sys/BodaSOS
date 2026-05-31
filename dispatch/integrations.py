from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

OTP_CACHE_PREFIX = "bodasos:otp:"
OTP_TTL_SECONDS = 300


@dataclass(frozen=True)
class SmsResult:
    ok: bool
    message: str
    payload: dict[str, Any] | None = None


def _otp_cache_key(phone_number: str) -> str:
    return f"{OTP_CACHE_PREFIX}{phone_number.strip()}"


def generate_otp_code() -> str:
    return f"{random.randint(0, 9999):04d}"


def store_otp_code(phone_number: str, code: str | None = None) -> str:
    otp = code or generate_otp_code()
    cache.set(_otp_cache_key(phone_number), otp, timeout=OTP_TTL_SECONDS)
    return otp


def verify_otp_code(phone_number: str, code: str) -> bool:
    cached_code = cache.get(_otp_cache_key(phone_number))
    return cached_code is not None and str(cached_code).strip() == str(code).strip()


def send_sms(phone_number: str, message: str) -> SmsResult:
    username = getattr(settings, "AFRICASTALKING_USERNAME", "")
    api_key = getattr(settings, "AFRICASTALKING_API_KEY", "")
    sender = getattr(settings, "AFRICASTALKING_SENDER_ID", "")
    sandbox = getattr(settings, "AFRICASTALKING_SANDBOX", True)

    if not username or not api_key:
        return SmsResult(ok=True, message="SMS mocked locally", payload={"phone_number": phone_number, "message": message})

    endpoint = "https://api.sandbox.africastalking.com/version1/messaging" if sandbox else "https://api.africastalking.com/version1/messaging"
    headers = {
        "apiKey": api_key,
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    data = {
        "username": username,
        "to": phone_number,
        "message": message,
        "from": sender,
    }
    response = requests.post(endpoint, headers=headers, data=data, timeout=15)
    response.raise_for_status()
    return SmsResult(ok=True, message="SMS sent", payload=response.json())


def send_rider_verification_sms(phone_number: str) -> tuple[str, SmsResult]:
    code = store_otp_code(phone_number)
    result = send_sms(phone_number, f"Your BodaSOS verification code is {code}. It expires in 5 minutes.")
    return code, result


def send_dispatch_alert_sms(phone_number: str, rider_name: str, distance_km: float) -> SmsResult:
    return send_sms(
        phone_number,
        f"BodaSOS dispatch: {rider_name} is en route. Distance: {distance_km:.1f} km.",
    )


def parse_sms_emergency_message(text: str) -> dict[str, str] | None:
    cleaned = " ".join(text.split())
    if not cleaned:
        return None

    parts = cleaned.split()
    keyword = parts[0].lower()
    if keyword not in {"help", "emergency", "bodasos"}:
        return None

    latitude = ""
    longitude = ""
    emergency_type = "other"
    notes = ""

    if len(parts) >= 3:
        latitude = parts[1]
        longitude = parts[2]
    if len(parts) >= 4:
        emergency_type = parts[3].lower()
    if len(parts) >= 5:
        notes = " ".join(parts[4:])

    return {
        "latitude": latitude,
        "longitude": longitude,
        "emergency_type": emergency_type,
        "notes": notes,
    }


def format_ussd_home() -> str:
    return (
        "CON BodaSOS\n"
        "1. Request emergency help\n"
        "2. Verify rider phone\n"
        "3. Demo rider dashboard"
    )


def format_ussd_help_prompt() -> str:
    return "CON Enter coordinates as lat,lon and optional note, for example -1.28,36.82 crash at the market"


def format_ussd_verify_prompt() -> str:
    return "CON Enter rider phone number and verification code separated by a comma"


def current_timestamp() -> str:
    return timezone.now().isoformat()
