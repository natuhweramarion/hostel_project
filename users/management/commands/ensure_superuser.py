"""
Idempotently create a superuser from environment variables.

Used on Render's free tier where there is no shell access. Runs from build.sh
on every deploy. If a user with the given username already exists, it does
nothing. If the env vars are missing, it logs a notice and exits cleanly so
the build is not broken.

Required env vars:
    DJANGO_SUPERUSER_USERNAME
    DJANGO_SUPERUSER_EMAIL
    DJANGO_SUPERUSER_PASSWORD
"""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a Django superuser from environment variables if one does not already exist."

    def handle(self, *args, **options):
        User = get_user_model()

        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not (username and email and password):
            self.stdout.write(self.style.WARNING(
                'ensure_superuser: DJANGO_SUPERUSER_* env vars not set; skipping.'
            ))
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS(
                f'ensure_superuser: superuser "{username}" already exists; nothing to do.'
            ))
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            is_manager=True,
        )
        self.stdout.write(self.style.SUCCESS(
            f'ensure_superuser: created superuser "{username}".'
        ))
