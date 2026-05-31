from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run the dispatch loop test harness."

    def handle(self, *args, **options):
        self.stdout.write("Dispatch loop test command placeholder")
