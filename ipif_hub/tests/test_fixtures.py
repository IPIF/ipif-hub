import pytest

from ipif_hub.models import Factoid


@pytest.mark.django_db(transaction=True)
def test_factoid_fixture(factoid):
    f = Factoid.objects.first()
    assert f.identifier == "http://test.com/factoids/factoid1"
