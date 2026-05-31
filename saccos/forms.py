from django import forms

from dispatch.models import Sacco


class SaccoForm(forms.ModelForm):
    class Meta:
        model = Sacco
        fields = ["name", "chairman_name", "chairman_phone"]
