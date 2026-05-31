from dispatch.models import EmergencyRequest


def patient_requests():
    return EmergencyRequest.objects.all()
