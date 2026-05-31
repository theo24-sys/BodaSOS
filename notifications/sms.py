import logging
import os


logger = logging.getLogger(__name__)


class AfricaTalkingSMSService:
    def __init__(self):
        self.api_key = os.getenv("AFRICASTALKING_API_KEY", "")
        self.username = os.getenv("AFRICASTALKING_USERNAME", "")
        self.sender_id = os.getenv("AFRICASTALKING_SENDER_ID", "")
        self.client = None
        try:
            import africastalking

            africastalking.initialize(self.username, self.api_key)
            self.client = africastalking.SMS
        except Exception as exc:  # pragma: no cover - runtime integration path
            logger.warning("Africa's Talking SMS init failed: %s", exc)

    def _send(self, phone_number, message):
        if self.client is None:
            logger.info("SMS fallback (no client) phone=%s message=%s", phone_number, message)
            return False
        try:
            response = self.client.send(message, [phone_number], sender_id=self.sender_id or None)
            logger.info("SMS sent phone=%s response=%s", phone_number, response)
            return True
        except Exception as exc:  # pragma: no cover - runtime integration path
            logger.exception("SMS send failed for %s: %s", phone_number, exc)
            return False

    def send_dispatch_sms(self, rider_phone, job):
        latitude = job.patient_location.y
        longitude = job.patient_location.x
        message = f"BodaSOS dispatch #{job.id}: {job.emergency_type} at https://maps.google.com/?q={latitude},{longitude}"
        return self._send(rider_phone, message)

    def send_sos_confirmation(self, patient_phone, rider_name, eta_minutes):
        message = f"BodaSOS: Rider {rider_name} is on the way. ETA {eta_minutes} minutes."
        return self._send(patient_phone, message)

    def send_fallback_sms(self, phone, payload_string):
        return self._send(phone, payload_string[:160])


_service = AfricaTalkingSMSService()


def send_dispatch_sms(rider_phone, job):
    return _service.send_dispatch_sms(rider_phone, job)


def send_sos_confirmation(patient_phone, rider_name, eta_minutes):
    return _service.send_sos_confirmation(patient_phone, rider_name, eta_minutes)


def send_fallback_sms(phone, payload_string):
    return _service.send_fallback_sms(phone, payload_string)
