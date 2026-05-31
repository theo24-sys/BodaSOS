from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .api import EmergencyRequestSerializer, NearestDispatchRequestSerializer, RiderSerializer
from .forms import EmergencyRequestForm, RiderForm, RiderVerificationForm, SaccoForm
from .integrations import (
    format_ussd_help_prompt,
    format_ussd_home,
    format_ussd_verify_prompt,
    parse_sms_emergency_message,
    send_rider_verification_sms,
    verify_otp_code,
)
from .models import EmergencyRequest, Rider, Sacco
from .services import assign_nearest_rider, find_nearest_rider


def _home_context():
    riders = Rider.objects.select_related("sacco").all()[:10]
    requests = EmergencyRequest.objects.select_related("assigned_rider", "assigned_rider__sacco")[:10]
    saccos = Sacco.objects.all()[:10]
    return {
        "rider_form": RiderForm(),
        "sacco_form": SaccoForm(),
        "emergency_form": EmergencyRequestForm(),
        "verification_form": RiderVerificationForm(),
        "riders": riders,
        "requests": requests,
        "saccos": saccos,
        "riders_json": [
            {
                "id": rider.id,
                "full_name": rider.full_name,
                "phone_number": rider.phone_number,
                "sacco_name": rider.sacco_name,
                "latitude": float(rider.latitude),
                "longitude": float(rider.longitude),
                "status": rider.status,
                "is_verified": rider.is_verified,
                "is_phone_verified": rider.is_phone_verified,
                "is_dispatch_ready": rider.is_dispatch_ready,
            }
            for rider in riders
        ],
        "requests_json": [
            {
                "id": request.id,
                "caller_name": request.caller_name,
                "emergency_type": request.emergency_type,
                "latitude": float(request.latitude),
                "longitude": float(request.longitude),
                "status": request.status,
                "assigned_rider": request.assigned_rider.full_name if request.assigned_rider else None,
            }
            for request in requests
        ],
    }


def home(request):
    return render(request, "dispatch/home.html", _home_context())


@require_http_methods(["GET", "POST"])
def rider_create(request):
    if request.method == "POST":
        form = RiderForm(request.POST, request.FILES)
        if form.is_valid():
            rider = form.save(commit=False)
            user, _ = User.objects.get_or_create(username=rider.phone_number)
            user.first_name = rider.full_name.split(" ")[0]
            user.last_name = " ".join(rider.full_name.split(" ")[1:])
            user.set_unusable_password()
            user.save()
            rider.user = user
            rider.status = Rider.DispatchStatus.INACTIVE
            rider.is_phone_verified = False
            rider.is_verified = False
            rider.save()
            send_rider_verification_sms(rider.phone_number)
            messages.success(request, f"Verification code sent to {rider.phone_number}. Complete the phone check to continue.")
            return redirect("rider_verify_phone")
    else:
        form = RiderForm()
    return render(request, "dispatch/form_page.html", {"form": form, "title": "Register Rider", "multipart": True})


@require_http_methods(["GET", "POST"])
def rider_verify_phone(request):
    if request.method == "POST":
        form = RiderVerificationForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data["phone_number"]
            code = form.cleaned_data["code"]
            rider = get_object_or_404(Rider, phone_number=phone_number)
            if verify_otp_code(phone_number, code):
                rider.is_phone_verified = True
                rider.save(update_fields=["is_phone_verified", "updated_at"])
                messages.success(request, "Phone verification complete. Your profile is now pending sacco and admin approval.")
                return redirect("rider_mobile_dashboard", rider_id=rider.id)
            messages.error(request, "Verification code did not match. Try again.")
    else:
        initial_phone = request.GET.get("phone_number", "")
        form = RiderVerificationForm(initial={"phone_number": initial_phone})
    return render(request, "dispatch/form_page.html", {"form": form, "title": "Verify Rider Phone"})


@require_http_methods(["GET", "POST"])
def emergency_request_create(request):
    if request.method == "POST":
        form = EmergencyRequestForm(request.POST)
        if form.is_valid():
            emergency = form.save(commit=False)
            emergency.request_source = EmergencyRequest.RequestSource.WEB
            emergency.save()
            assign_nearest_rider(emergency)
            messages.success(request, "Emergency request received and dispatched.")
            return redirect("home")
    else:
        form = EmergencyRequestForm()
    return render(request, "dispatch/form_page.html", {"form": form, "title": "Request Emergency Help"})


@require_http_methods(["GET", "POST"])
def rider_mobile_dashboard(request, rider_id: int):
    rider = get_object_or_404(Rider.objects.select_related("sacco"), pk=rider_id)
    if request.method == "POST":
        latitude = request.POST.get("latitude")
        longitude = request.POST.get("longitude")
        if latitude and longitude:
            rider.latitude = latitude
            rider.longitude = longitude
            rider.save(update_fields=["latitude", "longitude", "last_seen_at"])
            messages.success(request, "Location updated on the rider dashboard.")
        if request.POST.get("mark_active") == "1":
            rider.status = Rider.DispatchStatus.ACTIVE
            rider.save(update_fields=["status", "last_seen_at"])
            messages.success(request, "Rider set to active.")
        return redirect("rider_mobile_dashboard", rider_id=rider.id)
    return render(request, "dispatch/rider_mobile.html", {"rider": rider})


@require_http_methods(["GET", "POST"])
def sacco_dashboard(request, slug: str):
    sacco = get_object_or_404(Sacco, slug=slug)
    token = request.GET.get("token", "")
    if token != sacco.access_token:
        return HttpResponse("Invalid sacco dashboard token.", status=403)

    if request.method == "POST":
        rider = get_object_or_404(Rider, pk=request.POST.get("rider_id"), sacco=sacco)
        action = request.POST.get("action")
        if action == "approve":
            rider.sacco_approval_status = Rider.SaccoApprovalStatus.APPROVED
            rider.save(update_fields=["sacco_approval_status", "updated_at"])
            messages.success(request, f"Approved {rider.full_name}.")
        elif action == "reject":
            rider.sacco_approval_status = Rider.SaccoApprovalStatus.REJECTED
            rider.status = Rider.DispatchStatus.INACTIVE
            rider.save(update_fields=["sacco_approval_status", "status", "updated_at"])
            messages.warning(request, f"Rejected {rider.full_name}.")
        return redirect(f"{request.path}?token={token}")

    pending_riders = sacco.riders.filter(sacco_approval_status=Rider.SaccoApprovalStatus.PENDING)
    approved_riders = sacco.riders.filter(sacco_approval_status=Rider.SaccoApprovalStatus.APPROVED)
    return render(
        request,
        "dispatch/sacco_dashboard.html",
        {
            "sacco": sacco,
            "token": token,
            "pending_riders": pending_riders,
            "approved_riders": approved_riders,
        },
    )


@require_http_methods(["GET"])
def rider_list(request):
    riders = Rider.objects.select_related("sacco").all()
    return render(request, "dispatch/rider_list.html", {"riders": riders})


@require_http_methods(["POST"])
def nearest_dispatch_api(request):
    latitude = float(request.POST["latitude"])
    longitude = float(request.POST["longitude"])
    candidate = find_nearest_rider(latitude, longitude)
    if candidate is None:
        return JsonResponse({"status": "no_rider_found"}, status=404)
    return JsonResponse(
        {
            "status": "ok",
            "rider": {
                "id": candidate.rider.id,
                "full_name": candidate.rider.full_name,
                "phone_number": candidate.rider.phone_number,
                "distance_km": round(candidate.distance_km, 3),
            },
        }
    )


@api_view(["GET", "POST"])
def rider_api_list_create(request):
    if request.method == "GET":
        riders = Rider.objects.select_related("sacco").all().order_by("-last_seen_at", "full_name")
        return Response(RiderSerializer(riders, many=True).data)

    serializer = RiderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    rider = serializer.save()
    return Response(RiderSerializer(rider).data, status=201)


@api_view(["GET", "POST"])
def emergency_api_list_create(request):
    if request.method == "GET":
        emergencies = EmergencyRequest.objects.select_related("assigned_rider", "assigned_rider__sacco").all()
        return Response(EmergencyRequestSerializer(emergencies, many=True).data)

    serializer = EmergencyRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    emergency = serializer.save()
    assign_nearest_rider(emergency)
    return Response(EmergencyRequestSerializer(emergency).data, status=201)


@api_view(["POST"])
def nearest_dispatch_json(request):
    serializer = NearestDispatchRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    candidate = find_nearest_rider(
        serializer.validated_data["latitude"],
        serializer.validated_data["longitude"],
    )
    if candidate is None:
        return Response({"status": "no_rider_found"}, status=404)
    return Response(
        {
            "status": "ok",
            "rider": RiderSerializer(candidate.rider).data,
            "distance_km": round(candidate.distance_km, 3),
        }
    )


@require_http_methods(["POST"])
def sms_inbound_webhook(request):
    parsed = parse_sms_emergency_message(request.POST.get("text", ""))
    if not parsed:
        return JsonResponse({"status": "ignored"})

    emergency = EmergencyRequest.objects.create(
        caller_name=request.POST.get("from", "SMS User"),
        caller_phone=request.POST.get("from", ""),
        emergency_type=parsed["emergency_type"],
        latitude=parsed["latitude"] or 0,
        longitude=parsed["longitude"] or 0,
        notes=parsed["notes"],
        request_source=EmergencyRequest.RequestSource.SMS,
    )
    assign_nearest_rider(emergency)
    return JsonResponse({"status": "received", "request_id": emergency.id})


@require_http_methods(["POST"])
def ussd_webhook(request):
    text = request.POST.get("text", "")
    phone_number = request.POST.get("phoneNumber", request.POST.get("from", ""))
    parts = [part for part in text.split("*") if part] if text else []

    if not parts:
        return HttpResponse(format_ussd_home(), content_type="text/plain")

    if parts[0] == "1":
        if len(parts) == 1:
            return HttpResponse(format_ussd_help_prompt(), content_type="text/plain")
        if len(parts) >= 2:
            location_text = parts[1]
            note = " ".join(parts[2:]) if len(parts) > 2 else ""
            if "," not in location_text:
                return HttpResponse("END Invalid coordinates. Use lat,lon", content_type="text/plain")
            latitude_text, longitude_text = location_text.split(",", 1)
            emergency = EmergencyRequest.objects.create(
                caller_name=phone_number or "USSD User",
                caller_phone=phone_number,
                emergency_type=EmergencyRequest.EmergencyType.OTHER,
                latitude=latitude_text,
                longitude=longitude_text,
                notes=note,
                request_source=EmergencyRequest.RequestSource.USSD,
            )
            assign_nearest_rider(emergency)
            return HttpResponse(f"END Request logged. Ticket #{emergency.id}", content_type="text/plain")

    if parts[0] == "2":
        if len(parts) == 1:
            return HttpResponse(format_ussd_verify_prompt(), content_type="text/plain")
        if len(parts) >= 2 and "," in parts[1]:
            phone_text, code = parts[1].split(",", 1)
            rider = get_object_or_404(Rider, phone_number=phone_text.strip())
            if verify_otp_code(rider.phone_number, code):
                rider.is_phone_verified = True
                rider.save(update_fields=["is_phone_verified", "updated_at"])
                return HttpResponse("END Phone verified successfully", content_type="text/plain")
            return HttpResponse("END Verification code invalid", content_type="text/plain")

    return HttpResponse(format_ussd_home(), content_type="text/plain")
