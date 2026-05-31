def set_rider_duty_state(rider, is_active: bool):
    rider.status = "active" if is_active else "inactive"
    return rider
