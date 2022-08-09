import pytest
from django.test import override_settings
from django.core.management import call_command


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
