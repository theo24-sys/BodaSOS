import logging
from datetime import date

from django.db.models import Avg, Count

from notifications.services import trigger_mpesa_payout

from riders.models import Rider
from .models import Sacco, SaccoComplianceLog, SaccoPayoutBatch


logger = logging.getLogger(__name__)


def get_sacco_stats(sacco_id):
    sacco = Sacco.objects.get(pk=sacco_id)
    total_active_riders = Rider.objects.filter(sacco=sacco, duty_status=Rider.DutyStatus.ACTIVE).count()
    total_jobs = sacco.riders.filter(jobs__status="DELIVERED").count()
    return {
        "sacco_id": sacco.id,
        "total_active_riders": total_active_riders,
        "total_jobs_this_month": total_jobs,
        "average_response_time": 0,
        "pending_payout_amount": 0,
    }


def approve_payout_batch(batch_id, admin_user):
    batch = SaccoPayoutBatch.objects.get(pk=batch_id)
    batch.status = SaccoPayoutBatch.Status.APPROVED
    batch.approved_by = admin_user
    batch.save(update_fields=["status", "approved_by", "updated_at"])
    trigger_mpesa_payout(batch)
    return batch


def suspend_rider(rider_id, sacco_admin_user, reason):
    rider = Rider.objects.get(pk=rider_id)
    rider.duty_status = Rider.DutyStatus.OFFLINE
    rider.user.is_verified = False
    rider.user.save(update_fields=["is_verified"])
    rider.save(update_fields=["duty_status", "updated_at"])
    SaccoComplianceLog.objects.create(sacco=rider.sacco, rider=rider, event_type=SaccoComplianceLog.EventType.SUSPENSION, notes=reason)
    return rider
