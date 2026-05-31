import logging

from django.core.mail import send_mail

from . import tasks
from .push import send_push_notification
from .sms import send_fallback_sms


logger = logging.getLogger(__name__)


def send_dispatch_alert(rider, job):
	# enqueue the dispatch alert to Celery for background delivery and retries
	try:
		tasks.send_dispatch_alert_task.delay(rider.id, rider.phone, job.id, job.emergency_type)
		return True
	except Exception as exc:
		logger.exception("Failed to enqueue dispatch alert for rider %s: %s", rider.id, exc)
		# Fallback to synchronous send
		try:
			return send_push_notification(rider.user_id, "New dispatch", f"Emergency {job.emergency_type}")
		except Exception:
			return send_fallback_sms(rider.phone, f"BodaSOS dispatch #{job.id}")


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
	try:
		tasks.send_sos_confirmation_task.delay(job.id)
		return True
	except Exception:
		rider_name = job.assigned_rider.full_name if job.assigned_rider else "our rider"
		return send_fallback_sms(job.patient.phone, f"Rider {rider_name} is on the way.")
