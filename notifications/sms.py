def send_sms_message(phone_number: str, message: str) -> dict:
    return {"phone_number": phone_number, "message": message, "status": "queued"}
