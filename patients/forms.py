from django import forms

from dispatch.models import EmergencyRequest


class EmergencyRequestForm(forms.ModelForm):
    caller_name = forms.CharField(required=False)
    caller_phone = forms.CharField(required=False)
    device_session_id = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = EmergencyRequest
        fields = [
            "caller_name",
            "caller_phone",
            "device_session_id",
            "emergency_type",
            "latitude",
            "longitude",
            "notes",
        ]
