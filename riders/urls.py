from django.urls import path

from dispatch import views

urlpatterns = [
    path("onboard/", views.rider_create, name="rider_onboard"),
    path("new/", views.rider_create, name="rider_create"),
    path("verify/", views.rider_verify_phone, name="rider_verify_phone"),
    path("<int:rider_id>/mobile/", views.rider_mobile_dashboard, name="rider_mobile_dashboard"),
    path("list/", views.rider_list, name="rider_list"),
]
