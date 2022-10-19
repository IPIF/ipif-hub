import os
from code import interact

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand

from ipif_hub.models import IpifRepo


class Command(BaseCommand):
    help = "Ingests data from IPIF-Hub formatted JSON file"

    def handle(
        self,
        *args,
        endpoint_id: str = None,
        file_path: str = None,
        **options,
    ) -> None:
        os.environ["DJANGO_SUPERUSER_EMAIL"] = "test@test.com"
        os.environ["DJANGO_SUPERUSER_USERNAME"] = "rhadden"
        os.environ["DJANGO_SUPERUSER_PASSWORD"] = "whatever"

        call_command("clear_index", interactive=False, verbosity=0)
        call_command("flush", interactive=False, verbosity=0)
        call_command("createsuperuser", interactive=False, verbosity=0)

        user = User.objects.first()
        repo: IpifRepo = IpifRepo(
            endpoint_slug="test",
            endpoint_name="test",
            endpoint_uri="http://test.com",
            description="test",
            repo_active=True,
        )
        repo.save()
        repo.owners.add(user)
