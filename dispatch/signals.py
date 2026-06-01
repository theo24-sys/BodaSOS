from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync

try:
    from channels.layers import get_channel_layer
except Exception:
    get_channel_layer = None

from .models import EmergencyRequest, RiderProfile as Rider


def broadcast(payload: dict):
    if not get_channel_layer:
        return
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)("dashboard", {"type": "dashboard.update", "payload": payload})


@receiver(post_save, sender=EmergencyRequest)
def emergency_saved(sender, instance: EmergencyRequest, created, **kwargs):
    payload = {
        "type": "emergency",
        "id": instance.id,
        "latitude": float(instance.latitude),
        "longitude": float(instance.longitude),
        "status": instance.status,
        "created_at": instance.created_at.isoformat(),
    }
    broadcast({"event": "emergency_saved", "data": payload})


@receiver(post_save, sender=Rider)
def rider_saved(sender, instance: Rider, created, **kwargs):
    payload = {
        "type": "rider",
        "id": instance.id,
        "latitude": float(instance.latitude) if instance.latitude else None,
        "longitude": float(instance.longitude) if instance.longitude else None,
        "status": instance.status,
        "last_seen_at": instance.last_seen_at.isoformat() if instance.last_seen_at else None,
    }
    broadcast({"event": "rider_saved", "data": payload})
