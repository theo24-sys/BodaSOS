from django import forms

from .models import EmergencyRequest, RiderProfile, Sacco


class SaccoForm(forms.ModelForm):
    class Meta:
        model = Sacco
        fields = ["name", "chairman_name", "chairman_phone"]


class RiderOnboardingForm(forms.ModelForm):
    class Meta:
        model = RiderProfile
        fields = [
            "full_name",
            "phone_number",
            "national_id",
            "ntsa_license_number",
            "sacco",
            "latitude",
            "longitude",
            "profile_photo",
            "certificate_of_good_conduct",
            "sacco_membership_card",
            "is_trained_first_aid",
        ]


class RiderVerificationForm(forms.Form):
    phone_number = forms.CharField(max_length=32)
    code = forms.CharField(max_length=4)


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


RiderForm = RiderOnboardingForm
