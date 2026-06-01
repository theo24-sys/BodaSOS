from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ("phone_number", "role", "is_staff", "is_verified")
    list_filter = ("role", "is_staff", "is_verified", "sacco")
    search_fields = ("phone_number", "first_name", "last_name")
    ordering = ("phone_number",)
    fieldsets = (
        (None, {"fields": ("phone_number", "password")} ),
        ("Personal info", {"fields": ("first_name", "last_name", "email")} ),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")} ),
        ("BodaSOS", {"fields": ("role", "sacco", "pin", "is_verified")} ),
        ("Important dates", {"fields": ("last_login", "date_joined")} ),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone_number", "password1", "password2", "role", "sacco", "is_verified"),
        }),
    )
