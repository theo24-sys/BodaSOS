from __future__ import annotations

from celery import shared_task


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_dispatch_alert_task(self, rider_id, rider_phone, job_id, emergency_type):
    try:
        # import models lazily to avoid import-time DB/ORM issues
        from patients.models import Job
        from .push import send_push_notification
        from .sms import send_dispatch_sms

        job = Job.objects.get(pk=job_id)

        try:
            push_result = send_push_notification(rider_id, "New dispatch", f"Emergency {emergency_type}")
            if push_result:
                return True
        except Exception:
            pass

        return send_dispatch_sms(rider_phone, job)
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_sos_confirmation_task(self, job_id):
    try:
        from patients.models import Job
        from .sms import send_sos_confirmation

        job = Job.objects.select_related('patient', 'assigned_rider').get(pk=job_id)
        rider_name = job.assigned_rider.full_name if job.assigned_rider else 'our rider'
        return send_sos_confirmation(job.patient.phone, rider_name, 15)
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_fallback_sms_task(self, phone, message):
    try:
        from .sms import send_fallback_sms

        return send_fallback_sms(phone, message)
    except Exception as exc:
        raise self.retry(exc=exc)
