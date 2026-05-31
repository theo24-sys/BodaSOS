def validate_pin(pin: str, expected_pin: str) -> bool:
    return pin.strip() == expected_pin.strip()
