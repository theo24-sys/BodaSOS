from django import forms

from dispatch.models import EmergencyRequest


class EmergencyRequestForm(forms.ModelForm):
    class Meta:
        model = EmergencyRequest
        fields = [
            "caller_name",
            "caller_phone",
            "emergency_type",
            "latitude",
            "longitude",
            "notes",
        ]
