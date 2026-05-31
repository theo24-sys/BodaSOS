def send_push_notification(user_id: int, title: str, body: str) -> dict:
    return {"user_id": user_id, "title": title, "body": body, "status": "queued"}
