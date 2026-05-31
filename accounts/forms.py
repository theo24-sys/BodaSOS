from django import forms


class PinLoginForm(forms.Form):
    phone_number = forms.CharField(max_length=32)
    pin = forms.CharField(max_length=4, min_length=4)

    def clean_pin(self):
        pin = self.cleaned_data["pin"]
        if not pin.isdigit():
            raise forms.ValidationError("PIN must be 4 digits.")
        return pin
