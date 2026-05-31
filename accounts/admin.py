from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("phone_number", "role", "is_staff", "is_verified")
    ordering = ("phone_number",)
    fieldsets = UserAdmin.fieldsets + (("BodaSOS", {"fields": ("phone_number", "role", "sacco", "pin", "is_verified")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("BodaSOS", {"fields": ("phone_number", "role", "sacco", "is_verified")}),)
