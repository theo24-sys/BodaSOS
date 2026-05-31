from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from django.conf import settings
from django.db import transaction
from django.db import connection

from .models import EmergencyRequest, RiderProfile


@dataclass(frozen=True)
class DispatchCandidate:
    rider: RiderProfile
    distance_km: float


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * radius_km * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _dispatch_ready_queryset(riders: Iterable[RiderProfile] | None = None):
    queryset = riders if riders is not None else RiderProfile.objects.all()
    if hasattr(queryset, "filter"):
        return queryset.filter(
            status=RiderProfile.DispatchStatus.ACTIVE,
            is_phone_verified=True,
            is_verified=True,
            sacco_approval_status=RiderProfile.SaccoApprovalStatus.APPROVED,
        )
    return [
        rider
        for rider in queryset
        if rider.status == RiderProfile.DispatchStatus.ACTIVE
        and rider.is_phone_verified
        and rider.is_verified
        and rider.sacco_approval_status == RiderProfile.SaccoApprovalStatus.APPROVED
    ]


def _find_nearest_rider_python(latitude: float, longitude: float, riders: Iterable[RiderProfile]) -> DispatchCandidate | None:
    active_riders = list(riders)
    if not active_riders:
        return None

    closest_rider = min(
        active_riders,
        key=lambda rider: haversine_distance_km(
            latitude,
            longitude,
            float(rider.latitude),
            float(rider.longitude),
        ),
    )
    distance_km = haversine_distance_km(
        latitude,
        longitude,
        float(closest_rider.latitude),
        float(closest_rider.longitude),
    )
    return DispatchCandidate(rider=closest_rider, distance_km=distance_km)


def _find_nearest_rider_postgis(latitude: float, longitude: float) -> DispatchCandidate | None:
    table_name = RiderProfile._meta.db_table
    sql = f"""
        SELECT id,
               ST_Distance(
                   ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
                   ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography
               ) AS distance_m
        FROM {table_name}
        WHERE status = %s
          AND is_phone_verified = TRUE
          AND is_verified = TRUE
          AND sacco_approval_status = %s
        ORDER BY distance_m ASC
        LIMIT 1
    """
    with connection.cursor() as cursor:
        cursor.execute(
            sql,
            [
                longitude,
                latitude,
                RiderProfile.DispatchStatus.ACTIVE,
                RiderProfile.SaccoApprovalStatus.APPROVED,
            ],
        )
        row = cursor.fetchone()

    if row is None:
        return None

    rider = RiderProfile.objects.get(pk=row[0])
    return DispatchCandidate(rider=rider, distance_km=float(row[1]) / 1000.0)


def find_nearest_rider(
    latitude: float,
    longitude: float,
    riders: Iterable[RiderProfile] | None = None,
) -> DispatchCandidate | None:
    if riders is None and getattr(settings, "POSTGIS_ENABLED", False) and connection.vendor == "postgresql":
        candidate = _find_nearest_rider_postgis(latitude, longitude)
        if candidate is not None:
            return candidate

    queryset = _dispatch_ready_queryset(riders)
    return _find_nearest_rider_python(latitude, longitude, queryset)


@transaction.atomic
def assign_nearest_rider(request: EmergencyRequest) -> EmergencyRequest:
    candidate = find_nearest_rider(float(request.latitude), float(request.longitude))
    if candidate is None:
        request.status = EmergencyRequest.Status.NO_RIDER_FOUND
        request.assigned_rider = None
        request.save(update_fields=["status", "assigned_rider", "updated_at"])
        return request

    request.status = EmergencyRequest.Status.ASSIGNED
    request.assigned_rider = candidate.rider
    request.save(update_fields=["status", "assigned_rider", "updated_at"])
    return request
