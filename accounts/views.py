from django.contrib.auth import login, logout
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .forms import PinLoginForm


User = get_user_model()


@csrf_protect
@require_http_methods(["GET", "POST"])
def pin_login_view(request):
    form = PinLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = User.objects.filter(phone_number=form.cleaned_data["phone_number"]).first()
        if user and user.pin and check_password(form.cleaned_data["pin"], user.pin):
            login(request, user)
            return JsonResponse({"success": True, "role": user.role, "phone_number": user.phone_number})
        form.add_error(None, "Invalid phone number or PIN.")
    return render(request, "registration/login.html", {"form": form})


jwt_obtain_pair_view = TokenObtainPairView.as_view()
token_refresh_view = TokenRefreshView.as_view()


@require_http_methods(["POST", "GET"])
def logout_view(request):
    logout(request)
    request.session.flush()
    return JsonResponse({"success": True})


@require_http_methods(["GET"])
def whoami_view(request):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"authenticated": False}, status=401)
    return JsonResponse({"authenticated": True, "role": user.role, "phone_number": user.phone_number, "sacco_id": user.sacco_id})
