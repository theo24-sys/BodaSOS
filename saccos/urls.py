from django.urls import path

from dispatch import views

urlpatterns = [
    path("<slug:slug>/dashboard/", views.sacco_dashboard, name="sacco_dashboard"),
]
