from __future__ import annotations

import json
import logging

from django.contrib import messages
from django.contrib.auth.models import Group
from accounts.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.templatetags.static import static
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField

from patients.forms import EmergencyRequestForm
from riders.forms import RiderForm
from riders.forms import RiderVerificationForm
from saccos.forms import SaccoForm
from .api import EmergencyRequestSerializer, NearestDispatchRequestSerializer, RiderSerializer
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


logger = logging.getLogger(__name__)


def _user_role(user) -> str:
    if not user.is_authenticated:
        return "caller"
    if user.is_superuser:
        return "operator"
    if hasattr(user, "chairman_sacco"):
        return "chairman"
    if hasattr(user, "rider_profile"):
        return "rider"
    return "caller"


def _role_label(role: str) -> str:
    return {
        "operator": "Operator",
        "chairman": "Sacco Chairman",
        "rider": "Authenticated Rider",
        "caller": "Public Caller",
    }.get(role, "Public Caller")


def _require_authenticated_role(request, *, allow_admin: bool = True, allow_chairman: bool = False, allow_rider: bool = False) -> bool:
    if not request.user.is_authenticated:
        return False
    if allow_admin and request.user.is_superuser:
        return True
    if allow_chairman and hasattr(request.user, "chairman_sacco"):
        return True
    if allow_rider and hasattr(request.user, "rider_profile"):
        return True
    return False


def _base_public_context():
    return {
        "role_label": "Public Caller",
        "is_public_view": True,
    }


def _portal_context(request):
    role = _user_role(request.user)
    rider = getattr(request.user, "rider_profile", None)
    sacco = getattr(request.user, "chairman_sacco", None)
    rider_count = Rider.objects.count()
    sacco_count = Sacco.objects.count()
    emergency_count = EmergencyRequest.objects.count()
    return {
        "current_role": role,
        "role_label": _role_label(role),
        "rider_profile": rider,
        "chairman_sacco": sacco,
        "rider_count": rider_count,
        "sacco_count": sacco_count,
        "emergency_count": emergency_count,
        "portal_actions": [
            {"label": "Open emergency console", "href": reverse("home"), "tone": "primary"},
            {"label": "Rider registry", "href": reverse("rider_list"), "tone": "secondary"},
        ],
    }


def _home_context():
    return {
        "rider_form": RiderForm(),
        "emergency_form": EmergencyRequestForm(),
        "verification_form": RiderVerificationForm(),
    }


def home(request):
    if request.user.is_authenticated:
        return redirect("portal")
    return render(request, "dispatch/home.html", _home_context() | _base_public_context())


@login_required
def portal(request):
    return render(request, "dispatch/portal.html", _portal_context(request))


@never_cache
def web_manifest(request):
    return JsonResponse(
        {
            "name": "BodaSOS Emergency Dispatch",
            "short_name": "BodaSOS",
            "description": "Mobile-first emergency dispatch for Kenyan boda boda networks.",
            "start_url": "/",
            "scope": "/",
            "display": "standalone",
            "background_color": "#111827",
            "theme_color": "#EF4444",
            "icons": [
                {
                    "src": static("images/bodasos-icon.png"),
                    "sizes": "192x192",
                    "type": "image/png",
                },
                {
                    "src": static("images/bodasos-icon.png"),
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any maskable",
                },
            ],
        }
    )


@never_cache
def service_worker(request):
    script = """
const CACHE_NAME = 'bodasos-shell-v1';
const CORE_ASSETS = ['/', '/login/', '/static/manifest.json', '/static/images/bodasos-icon.png', '/static/images/bodasos-bg.png', '/service-worker.js'];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return Promise.allSettled(
                CORE_ASSETS.map((url) =>
                    fetch(url)
                        .then((response) => {
                            if (!response.ok) {
                                throw new Error(`Failed to fetch ${url}: ${response.status}`);
                            }
                            return cache.put(url, response);
                        })
                        .catch((error) => {
                            console.warn('Service worker cache failed:', url, error);
                            return null;
                        })
                )
            );
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
    if (event.request.method !== 'GET') {
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then((response) => {
                const clone = response.clone();
                caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
                return response;
            })
            .catch(() => caches.match(event.request).then((cached) => cached || caches.match('/')))
    );
});
"""
    return HttpResponse(script, content_type="application/javascript")


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
            rider_group, _ = Group.objects.get_or_create(name="rider")
            user.groups.add(rider_group)
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
                messages.success(request, "Phone verification complete. Your profile is now pending sacco and operator approval.")
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
    if not request.user.is_authenticated:
        return redirect(f"{reverse('login')}?next={request.path}")
    if not (request.user.is_superuser or getattr(request.user, "rider_profile", None) == rider):
        return HttpResponse("You do not have permission to view this rider dashboard.", status=403)
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
    if not request.user.is_authenticated:
        return redirect(f"{reverse('login')}?next={request.path}")
    if not (request.user.is_superuser or hasattr(request.user, "chairman_sacco") and request.user.chairman_sacco == sacco):
        return HttpResponse("You do not have permission to view this sacco dashboard.", status=403)
    token = request.GET.get("token", "")
    if token != sacco.access_token:
        return HttpResponse("Invalid sacco dashboard token.", status=403)

    if request.method == "POST":
        # allow sacco admins to approve/reject or create riders
        if request.POST.get("action") == "create_rider":
            phone = request.POST.get("new_rider_phone")
            full_name = request.POST.get("new_rider_name")
            if phone and full_name and (request.user.is_superuser or getattr(request.user, "chairman_sacco", None) == sacco):
                # create user and rider profile
                from accounts.services import create_rider_account

                user = create_rider_account(phone, sacco.id, full_name)
                Rider.objects.create(user=user, sacco=sacco, full_name=full_name, phone=phone)
                messages.success(request, f"Created rider {full_name} ({phone}).")
            else:
                messages.error(request, "Missing or invalid rider details.")
            return redirect(f"{request.path}?token={token}")

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
    if not _require_authenticated_role(request, allow_admin=True, allow_chairman=True):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
        return HttpResponse("You do not have permission to view this rider list.", status=403)
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
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required."}, status=403)
        riders = Rider.objects.select_related("sacco").all().order_by("-last_seen_at", "full_name")
        return Response(RiderSerializer(riders, many=True).data)

    serializer = RiderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    rider = serializer.save()
    return Response(RiderSerializer(rider).data, status=201)


@api_view(["GET", "POST"])
def emergency_api_list_create(request):
    if request.method == "GET":
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required."}, status=403)
        emergencies = EmergencyRequest.objects.select_related("assigned_rider", "assigned_rider__sacco").all()
        return Response(EmergencyRequestSerializer(emergencies, many=True).data)

    serializer = EmergencyRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    emergency = serializer.save()
    assign_nearest_rider(emergency)
    return Response(EmergencyRequestSerializer(emergency).data, status=201)


@login_required
def dashboard(request):
    """Render a lightweight dashboard for operators and riders."""
    ctx = _portal_context(request)
    return render(request, "dispatch/dashboard.html", ctx)


@require_http_methods(["GET"])
def dashboard_metrics_api(request):
    """Return aggregated metrics for dashboards as JSON."""
    if not _require_authenticated_role(request, allow_admin=True, allow_chairman=True):
        return JsonResponse({"detail": "Authentication required."}, status=403)

    total_emergencies = EmergencyRequest.objects.count()
    pending = EmergencyRequest.objects.filter(status=EmergencyRequest.Status.PENDING).count()
    assigned = EmergencyRequest.objects.filter(status=EmergencyRequest.Status.ASSIGNED).count()
    completed = EmergencyRequest.objects.filter(status=EmergencyRequest.Status.COMPLETED).count()
    no_rider = EmergencyRequest.objects.filter(status=EmergencyRequest.Status.NO_RIDER_FOUND).count()

    active_riders = Rider.objects.filter(status=Rider.DispatchStatus.ACTIVE).count()

    # average response time (completed requests)
    avg_seconds = None
    try:
        avg_duration = (
            EmergencyRequest.objects.filter(status=EmergencyRequest.Status.COMPLETED)
            .annotate(duration=ExpressionWrapper(F("updated_at") - F("created_at"), output_field=DurationField()))
            .aggregate(avg=Avg("duration"))
        )
        if avg_duration and avg_duration.get("avg"):
            # avg_duration['avg'] is a timedelta
            avg_seconds = int(avg_duration["avg"].total_seconds())
    except Exception as e:
        logger.debug("Could not compute avg response duration: %s", e)
        avg_seconds = None

    types = list(
        EmergencyRequest.objects.values("emergency_type").annotate(count=Count("id")).order_by("emergency_type")
    )

    anonymous_triggers = EmergencyRequest.objects.filter(device_session_id__isnull=False).exclude(device_session_id="").count()
    confirmed_dispatches = EmergencyRequest.objects.filter(device_session_id__isnull=False).exclude(device_session_id="").filter(
        status__in=[EmergencyRequest.Status.ASSIGNED, EmergencyRequest.Status.COMPLETED]
    ).count()
    resolved_requests = EmergencyRequest.objects.filter(device_session_id__isnull=False).exclude(device_session_id="").filter(
        status=EmergencyRequest.Status.COMPLETED
    ).count()

    data = {
        "total_emergencies": total_emergencies,
        "pending": pending,
        "assigned": assigned,
        "completed": completed,
        "no_rider": no_rider,
        "active_riders": active_riders,
        "avg_response_seconds": avg_seconds,
        "by_type": types,
        "funnel": {
            "anonymous_triggers": anonymous_triggers,
            "confirmed_dispatches": confirmed_dispatches,
            "resolved_requests": resolved_requests,
        },
    }
    return JsonResponse(data)


@require_http_methods(["GET"])
def dashboard_active_emergencies(request):
    if not _require_authenticated_role(request, allow_admin=True, allow_chairman=True):
        return JsonResponse({"detail": "Authentication required."}, status=403)

    qs = EmergencyRequest.objects.filter(status=EmergencyRequest.Status.PENDING).order_by("-created_at")[:500]
    items = []
    for e in qs:
        items.append(
            {
                "id": e.id,
                "latitude": float(e.latitude),
                "longitude": float(e.longitude),
                "created_at": e.created_at.isoformat(),
                "emergency_type": e.emergency_type,
            }
        )
    return JsonResponse({"items": items})


@require_http_methods(["GET"])
def dashboard_riders(request):
    if not _require_authenticated_role(request, allow_admin=True, allow_chairman=True):
        return JsonResponse({"detail": "Authentication required."}, status=403)

    qs = Rider.objects.filter(status=Rider.DispatchStatus.ACTIVE).order_by("-last_seen_at")[:1000]
    items = []
    for r in qs:
        items.append(
            {
                "id": r.id,
                "full_name": r.full_name,
                "phone_number": r.phone_number,
                "latitude": float(r.latitude),
                "longitude": float(r.longitude),
                "last_seen_at": r.last_seen_at.isoformat(),
            }
        )
    return JsonResponse({"items": items})


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
def anonymous_trigger(request):
    """Accept a short anonymous trigger from a patient device.

    Expects JSON or form POST with `device_session_id`, `latitude`, `longitude`, and optional `note`.
    Creates an EmergencyRequest with the device_session_id so it can be tracked in dashboards.
    """
    data = request.POST or json.loads(request.body.decode("utf-8") or "{}")
    device_session = data.get("device_session_id") or data.get("device_id")
    lat = data.get("latitude")
    lon = data.get("longitude")
    note = data.get("note", "")

    if not device_session or not lat or not lon:
        return JsonResponse({"status": "error", "detail": "Missing device_session_id or coordinates."}, status=400)

    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except Exception:
        return JsonResponse({"status": "error", "detail": "Invalid coordinates."}, status=400)

    emergency = EmergencyRequest.objects.create(
        device_session_id=device_session,
        latitude=lat_f,
        longitude=lon_f,
        emergency_type=EmergencyRequest.EmergencyType.OTHER,
        caller_name="Anonymous",
        caller_phone="",
        request_source=EmergencyRequest.RequestSource.WEB,
        notes=note,
    )

    # attempt to assign nearest rider asynchronously
    try:
        assign_nearest_rider(emergency)
    except Exception as e:
        logger.debug("Could not assign nearest rider for anonymous trigger: %s", e)

    return JsonResponse({"status": "ok", "id": emergency.id})


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
