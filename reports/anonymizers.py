import hashlib


def anonymize_job(job):
    phone = job.patient.phone if job.patient_id else ""
    hashed_phone = hashlib.sha256(phone.encode("utf-8")).hexdigest() if phone else ""
    return {
        "sha_job_code": job.sha_job_code,
        "emergency_type": job.emergency_type,
        "county": getattr(getattr(job.assigned_rider, "sacco", None), "county", ""),
        "sub_county": getattr(getattr(job.assigned_rider, "sacco", None), "sub_county", ""),
        "dispatch_time_seconds": 0,
        "delivered_at": job.delivered_at,
        "anonymized_patient_id": hashed_phone,
        "rider_id": f"rider-{job.assigned_rider_id}" if job.assigned_rider_id else "",
        "outcome": job.status,
    }
