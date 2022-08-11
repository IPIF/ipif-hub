import pytest
from rest_framework.test import APIClient
from ipif_hub.serializers import PersonSerializer

from ipif_hub.tests.conftest import (
    factoid,
    person,
    source,
    statement,
    person2,
    statement2,
    factoid2,
)


@pytest.mark.django_db(transaction=True)
def test_request_for_persons(person, factoid):
    client = APIClient()
    response = client.get("/ipif/persons/")
    assert response.data == [PersonSerializer(person).data]

    response = client.get("/testrepo/ipif/persons/")
    assert response.data == [PersonSerializer(person).data]
