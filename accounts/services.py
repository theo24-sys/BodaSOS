import logging
from datetime import timedelta

from django.contrib.auth.hashers import check_password
from django.core import signing
from django.utils import timezone

from .models import User


logger = logging.getLogger(__name__)


def issue_sos_token(phone_number):
    payload = {"phone_number": phone_number, "issued_at": timezone.now().isoformat()}
    return signing.dumps(payload, salt="bodasos-sos-token")


def validate_pin(user, pin):
    return bool(user and user.pin and check_password(pin, user.pin))


def create_rider_account(phone, sacco_id, name):
    return User.objects.create_user(phone_number=phone, role=User.Roles.RIDER, sacco_id=sacco_id, first_name=name, is_verified=True)


def create_sacco_admin(phone, sacco_id, name):
    return User.objects.create_user(phone_number=phone, role=User.Roles.SACCO_ADMIN, sacco_id=sacco_id, first_name=name, is_verified=True)
