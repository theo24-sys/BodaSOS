def anonymize_dispatch_row(row: dict) -> dict:
    redacted = dict(row)
    redacted.pop("caller_name", None)
    redacted.pop("caller_phone", None)
    redacted.pop("latitude", None)
    redacted.pop("longitude", None)
    return redacted
