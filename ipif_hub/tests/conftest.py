import pytest
from django.test import override_settings
from django.core.management import call_command

from ipif_hub.models import IpifRepo
import datetime


@pytest.fixture(autouse=True)
@pytest.mark.django_db
def setup():
    with override_settings(
        CELERY_ALWAYS_EAGER=True,
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        broker_url="memory://",
        backend="memory",
    ):
        call_command("clear_index", interactive=False, verbosity=0)
        yield
        call_command("clear_index", interactive=False, verbosity=0)


test_repo_no_slug = {
    "endpoint_name": "TestRepo",
    "endpoint_uri": "http://test.com/",
    "refresh_frequency": "daily",
    "refresh_time": datetime.time(0, 0, 0),
    "endpoint_is_ipif": False,
    "description": "A test repo",
    "provider": "University of Test",
}


@pytest.fixture
def repo():
    # Create a repo
    repo = IpifRepo(endpoint_slug="testrepo", **test_repo_no_slug)
    repo.save()
    yield repo
