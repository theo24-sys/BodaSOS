import logging

from django.core import signing
from django.utils import timezone

from dispatch.services import trigger_dispatch

from .models import Job, Patient


logger = logging.getLogger(__name__)


def _build_location(lat, lon):
    try:
        from django.contrib.gis.geos import Point

        return Point(float(lon), float(lat), srid=4326)
    except Exception:
        return f"{lat},{lon}"


def create_sos_job(lat, lon, emergency_type, phone, session_token):
    token_payload = signing.loads(session_token, salt="bodasos-sos-token", max_age=7200)
    if token_payload.get("phone_number") != phone:
        raise ValueError("Invalid SOS session token")

    patient, _ = Patient.objects.get_or_create(phone=phone)
    job = Job.objects.create(
        patient=patient,
        emergency_type=emergency_type,
        patient_location=_build_location(lat, lon),
        session_token=session_token,
    )
    trigger_dispatch(job)
    return job.id


def cancel_job(job_id, reason):
    job = Job.objects.get(pk=job_id)
    job.status = Job.Status.CANCELLED
    job.cancellation_reason = reason
    job.save(update_fields=["status", "cancellation_reason", "updated_at"])
    logger.info("Cancelled job %s reason=%s", job_id, reason)
    return job


def mark_delivered(job_id, rider_id):
    job = Job.objects.select_related("assigned_rider").get(pk=job_id)
    job.status = Job.Status.DELIVERED
    job.delivered_at = timezone.now()
    job.save(update_fields=["status", "delivered_at", "updated_at"])
    logger.info("Job %s delivered by rider %s", job_id, rider_id)
    return job
