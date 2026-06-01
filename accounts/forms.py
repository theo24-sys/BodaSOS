from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import User


class PinLoginForm(forms.Form):
    phone_number = forms.CharField(max_length=32)
    pin = forms.CharField(max_length=4, min_length=4)

    def clean_pin(self):
        pin = self.cleaned_data["pin"]
        if not pin.isdigit():
            raise forms.ValidationError("PIN must be 4 digits.")
        return pin


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("phone_number", "role", "sacco", "is_verified")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("phone_number", "role", "sacco", "pin", "is_verified")
