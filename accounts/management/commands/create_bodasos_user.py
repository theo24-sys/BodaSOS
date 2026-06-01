import getpass

from django.core.management.base import BaseCommand, CommandError

from accounts.models import User
from saccos.models import Sacco


class Command(BaseCommand):
    help = "Create a BodaSOS user with phone-number login credentials."

    def add_arguments(self, parser):
        parser.add_argument("--phone", required=True, help="Phone number to use as the login identifier.")
        parser.add_argument(
            "--role",
            choices=[choice.value for choice in User.Roles],
            default=User.Roles.SYSTEM_ADMIN,
            help="User role to create.",
        )
        parser.add_argument("--password", help="Password for the new user. If omitted, the command will prompt.")
        parser.add_argument(
            "--sacco",
            help="Sacco registration number or name for rider or sacco_admin accounts.",
        )
        parser.add_argument("--first-name", default="", help="User first name.")
        parser.add_argument("--last-name", default="", help="User last name.")

    def handle(self, *args, **options):
        phone = options["phone"].strip()
        role = options["role"]
        password = options["password"]
        sacco_slug = options["sacco"]
        first_name = options["first_name"].strip()
        last_name = options["last_name"].strip()

        if User.objects.filter(phone_number=phone).exists():
            raise CommandError(f"A user with phone number {phone} already exists.")

        if role in {User.Roles.RIDER, User.Roles.SACCO_ADMIN} and not sacco_slug:
            raise CommandError("The --sacco option is required for rider and sacco_admin accounts.")

        sacco = None
        if sacco_slug:
            try:
                sacco = Sacco.objects.get(registration_number=sacco_slug)
            except Sacco.DoesNotExist:
                try:
                    sacco = Sacco.objects.get(name=sacco_slug)
                except Sacco.DoesNotExist:
                    raise CommandError(
                        f"Sacco with registration number or name '{sacco_slug}' does not exist."
                    )

        if not password:
            password = getpass.getpass("Password: ")
            password_confirm = getpass.getpass("Password (again): ")
            if password != password_confirm:
                raise CommandError("Passwords do not match.")

        extra_fields = {
            "first_name": first_name,
            "last_name": last_name,
            "is_verified": True,
        }
        if sacco is not None:
            extra_fields["sacco"] = sacco

        if role == User.Roles.SYSTEM_ADMIN:
            user = User.objects.create_superuser(phone_number=phone, password=password, **extra_fields)
        else:
            user = User.objects.create_user(phone_number=phone, password=password, role=role, **extra_fields)

        self.stdout.write(self.style.SUCCESS("Created BodaSOS user:"))
        self.stdout.write(f"  phone_number: {user.phone_number}")
        self.stdout.write(f"  role: {user.role}")
        if user.sacco:
            self.stdout.write(
                f"  sacco: {user.sacco.name} (registration_number: {user.sacco.registration_number})"
            )
        self.stdout.write("Use these credentials to sign in at the staff portal.")
