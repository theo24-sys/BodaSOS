from dispatch.models import EmergencyRequest


def build_sha_claim_payload(emergency: EmergencyRequest) -> dict:
    return {
        "sha_triage_code": emergency.emergency_type,
        "created_at": emergency.created_at.isoformat() if emergency.created_at else None,
    }
