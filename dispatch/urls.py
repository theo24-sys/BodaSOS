from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("portal/", views.portal, name="portal"),
    path("manifest.webmanifest", views.web_manifest, name="web_manifest"),
    path("service-worker.js", views.service_worker, name="service_worker"),
    path("riders/", views.rider_list, name="rider_list"),
    path("riders/onboard/", views.rider_create, name="rider_onboard"),
    path("riders/new/", views.rider_create, name="rider_create"),
    path("riders/verify/", views.rider_verify_phone, name="rider_verify_phone"),
    path("riders/<int:rider_id>/mobile/", views.rider_mobile_dashboard, name="rider_mobile_dashboard"),
    path("saccos/<slug:slug>/dashboard/", views.sacco_dashboard, name="sacco_dashboard"),
    path("requests/new/", views.emergency_request_create, name="emergency_request_create"),
    path("api/dispatch/nearest/", views.nearest_dispatch_api, name="nearest_dispatch_api"),
    path("api/riders/", views.rider_api_list_create, name="rider_api_list_create"),
    path("api/emergencies/", views.emergency_api_list_create, name="emergency_api_list_create"),
    path("api/dispatch/nearest-json/", views.nearest_dispatch_json, name="nearest_dispatch_json"),
    path("api/africastalking/sms/", views.sms_inbound_webhook, name="sms_inbound_webhook"),
    path("api/africastalking/ussd/", views.ussd_webhook, name="ussd_webhook"),
]
