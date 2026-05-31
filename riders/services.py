import logging
from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from patients.models import Job
from saccos.models import SaccoComplianceLog

from .models import DispatchMiss, Rider, RiderLocationLog


logger = logging.getLogger(__name__)


def _build_location(lat, lon):
    try:
        from django.contrib.gis.geos import Point

        return Point(float(lon), float(lat), srid=4326)
    except Exception:
        return f"{lat},{lon}"


@transaction.atomic
def update_rider_location(rider_id, lat, lon):
    rider = Rider.objects.select_related("sacco").get(pk=rider_id)
    rider.current_location = None if lat is None or lon is None else _build_location(lat, lon)
    rider.last_ping = timezone.now()
    rider.save(update_fields=["current_location", "last_ping", "updated_at"])
    RiderLocationLog.objects.create(rider=rider, location=rider.current_location)
    return rider


def set_duty_status(rider_id, status):
    rider = Rider.objects.get(pk=rider_id)
    rider.duty_status = status
    rider.last_ping = timezone.now()
    rider.save(update_fields=["duty_status", "last_ping", "updated_at"])
    return rider


def mark_dispatch_missed(rider_id, job_id):
    rider = Rider.objects.select_related("sacco").get(pk=rider_id)
    job = Job.objects.get(pk=job_id)
    DispatchMiss.objects.create(rider=rider, job=job)
    rider.dispatch_miss_count += 1
    rider.save(update_fields=["dispatch_miss_count", "updated_at"])
    recent_misses = DispatchMiss.objects.filter(rider=rider, missed_at__gte=timezone.now() - timedelta(hours=24)).count()
    if recent_misses >= 3 and rider.sacco_id:
        SaccoComplianceLog.objects.create(sacco=rider.sacco, rider=rider, event_type=SaccoComplianceLog.EventType.DISPATCH_MISS, notes="3 dispatch misses within 24 hours")
    return rider


def accept_dispatch(rider_id, job_id):
    rider = Rider.objects.get(pk=rider_id)
    job = Job.objects.select_related("assigned_rider").get(pk=job_id)
    rider.duty_status = Rider.DutyStatus.IN_TRANSIT
    rider.last_ping = timezone.now()
    rider.save(update_fields=["duty_status", "last_ping", "updated_at"])
    job.status = Job.Status.DISPATCHED
    job.accepted_at = timezone.now()
    job.assigned_rider = rider
    job.save(update_fields=["status", "accepted_at", "assigned_rider", "updated_at"])
    return job
