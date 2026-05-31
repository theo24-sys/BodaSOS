from django import forms

from dispatch.models import RiderProfile


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


RiderForm = RiderOnboardingForm
