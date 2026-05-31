from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.contrib.auth.hashers import make_password
from django.db import models


class UserManager(DjangoUserManager):
    use_in_migrations = True

    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError("The phone_number must be set.")
        extra_fields.setdefault("role", User.Roles.PATIENT)
        user = self.model(phone_number=phone_number, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Roles.SYSTEM_ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)
        return self.create_user(phone_number, password=password, **extra_fields)


class User(AbstractUser):
    class Roles(models.TextChoices):
        PATIENT = "patient", "Patient"
        RIDER = "rider", "Rider"
        SACCO_ADMIN = "sacco_admin", "Sacco Admin"
        SYSTEM_ADMIN = "system_admin", "System Admin"

    username = None
    phone_number = models.CharField(max_length=32, unique=True)
    role = models.CharField(max_length=32, choices=Roles.choices, default=Roles.PATIENT)
    sacco = models.ForeignKey("saccos.Sacco", null=True, blank=True, on_delete=models.SET_NULL, related_name="users")
    pin = models.CharField(max_length=128, blank=True, default="")
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def set_pin(self, pin):
        self.pin = make_password(pin)
        self.save(update_fields=["pin"])
