def format_patient_request_summary(request_obj) -> dict:
    return {"id": request_obj.id, "status": request_obj.status}
