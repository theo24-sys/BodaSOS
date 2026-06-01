from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from decouple import config


class Command(BaseCommand):
    help = "Programmatically instantiates an internal operations superuser"

    def add_arguments(self, parser):
        parser.add_argument(
            "--phone",
            default=config("OPS_ADMIN_PHONE", "+254700000000"),
            help="Phone number for the operations superuser.",
        )
        parser.add_argument(
            "--password",
            default=config("OPS_ADMIN_PASSWORD", "SecureProdPassword123!"),
            help="Password for the operations superuser.",
        )

    def handle(self, *args, **options):
        User = get_user_model()
        phone = options["phone"].strip()
        password = options["password"]

        if User.objects.filter(phone_number=phone).exists():
            self.stdout.write(self.style.WARNING(f"User with phone {phone} already exists."))
            return

        User.objects.create_superuser(
            phone_number=phone,
            password=password,
            role=User.Roles.SYSTEM_ADMIN,
        )

        self.stdout.write(self.style.SUCCESS("Obfuscated admin account created successfully."))
