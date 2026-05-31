from django.shortcuts import render


def patient_shell_view(request):
    return render(request, "pwa/patient.html")
