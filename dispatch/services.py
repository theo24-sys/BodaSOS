from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.core.cache import cache
from django.utils import timezone

from .models import DispatchAttempt, EmergencyRequest
from riders.models import Rider
from notifications.services import send_dispatch_alert


def get_nearest_rider(location, exclude_rider_ids=[]):
    """
    Executes a high-efficiency PostGIS Nearest Neighbor computation using
    the spatial GiST index bounding boxes.
    """
    return Rider.objects.filter(
        duty_status='ACTIVE'
    ).exclude(
        id__in=exclude_rider_ids
    ).annotate(
        distance=Distance('current_location', location)
    ).order_by('distance').first()


def find_nearest_rider(latitude, longitude):
    """
    Find nearest rider by latitude/longitude coordinates.
    Returns a candidate object with rider and distance_km attributes.
    """
    from collections import namedtuple
    
    # Create a point from coordinates
    location = Point(float(longitude), float(latitude))
    
    # Find nearest active rider
    rider = Rider.objects.filter(
        status=Rider.DispatchStatus.ACTIVE
    ).annotate(
        distance=Distance('point', location)
    ).order_by('distance').first()
    
    if not rider:
        return None
    
    # Return a named tuple with rider and distance_km for compatibility
    Candidate = namedtuple('Candidate', ['rider', 'distance_km'])
    distance_km = rider.distance.km if rider.distance else 0
    return Candidate(rider=rider, distance_km=distance_km)


def assign_nearest_rider(emergency):
    """
    Assign the nearest available rider to an emergency request.
    """
    if not isinstance(emergency, EmergencyRequest):
        return None
    
    # Find nearest rider
    location = Point(float(emergency.longitude), float(emergency.latitude))
    rider = Rider.objects.filter(
        status=Rider.DispatchStatus.ACTIVE
    ).annotate(
        distance=Distance('point', location)
    ).order_by('distance').first()
    
    if rider:
        emergency.assigned_rider = rider
        emergency.status = EmergencyRequest.Status.ASSIGNED
        emergency.save()
        # Send notification to rider
        send_dispatch_alert(rider, emergency)
    else:
        emergency.status = EmergencyRequest.Status.NO_RIDER_FOUND
        emergency.save()
    
    return emergency


def trigger_dispatch(job):
    exclusions = list(DispatchAttempt.objects.filter(job=job).values_list('rider_id', flat=True))
    rider = get_nearest_rider(job.patient_location, exclude_rider_ids=exclusions)

    if not rider:
        job.status = 'CANCELLED'
        job.save()
        return None

    attempt = DispatchAttempt.objects.create(
        job=job,
        rider=rider,
        attempt_number=len(exclusions) + 1
    )

    send_dispatch_alert(rider, job)

    # Track transient states strictly inside serverless caching layer
    cache.set(f"dispatch:{job.id}", rider.id, timeout=45)
    return attempt


def handle_dispatch_timeout(job_id):
    from riders.services import mark_dispatch_missed
    from patients.models import Job

    rider_id = cache.get(f"dispatch:{job_id}")
    if rider_id:
        cache.delete(f"dispatch:{job_id}")
        job = Job.objects.get(id=job_id)

        DispatchAttempt.objects.filter(job=job, rider_id=rider_id, status='SENT').update(
            status='MISSED', responded_at=timezone.now()
        )
        mark_dispatch_missed(rider_id, job_id)

        attempts = DispatchAttempt.objects.filter(job=job).count()
        if attempts >= 5:
            job.status = 'CANCELLED'
            job.save()
        else:
            trigger_dispatch(job)
