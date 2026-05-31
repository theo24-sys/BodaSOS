import logging

from django.core.mail import send_mail

from .push import send_push_notification
from .sms import send_dispatch_sms, send_fallback_sms, send_sos_confirmation as sms_send_sos_confirmation


logger = logging.getLogger(__name__)


def send_dispatch_alert(rider, job):
	try:
		push_result = send_push_notification(rider.user_id, "New dispatch", f"Emergency {job.emergency_type}")
		if push_result:
			return True
	except Exception as exc:  # pragma: no cover - integration path
		logger.warning("Push failed for rider %s: %s", rider.id, exc)
	return send_dispatch_sms(rider.phone, job)


def send_expiry_alert(rider):
	message = "BodaSOS: your first aid certification is expiring soon."
	send_fallback_sms(rider.phone, message)
	if rider.sacco and rider.sacco.users.filter(role="sacco_admin").exists():
		admin = rider.sacco.users.filter(role="sacco_admin").first()
		if admin.email:
			send_mail("Certification expiry", message, None, [admin.email])
	return True


def trigger_mpesa_payout(batch):
	logger.info("Triggering payout for batch %s", batch.id)
	admin = batch.sacco.users.filter(role="sacco_admin").first()
	if admin:
		send_fallback_sms(admin.phone_number, f"Payout batch {batch.id} approved for {batch.sacco.name}")
	return batch


def send_sos_confirmation(job):
	rider_name = job.assigned_rider.full_name if job.assigned_rider else "our rider"
	return sms_send_sos_confirmation(job.patient.phone, rider_name, 15)
