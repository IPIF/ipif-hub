import pytest
from rest_framework.test import APIClient

from ipif_hub.serializers import (
    FactoidSerializer,
    PersonSerializer,
    SourceSerializer,
    StatementSerializer,
)


@pytest.mark.django_db(transaction=True)
def test_request_for_persons(person, factoid):
    client = APIClient()
    response = client.get("/ipif/persons/")
    assert response.data == [PersonSerializer(person).data]

    response = client.get("/testrepo/ipif/persons/")
    assert response.data == [PersonSerializer(person).data]


@pytest.mark.django_db(transaction=True)
def test_request_for_specific_persons(person, factoid):
    client = APIClient()
    response = client.get("/ipif/persons/http://test.com/persons/person1")
    assert response.data == PersonSerializer(person).data

    response = client.get("/testrepo/ipif/persons/person1")
    assert response.data == PersonSerializer(person).data


@pytest.mark.django_db(transaction=True)
def test_request_for_statements(statement, factoid):
    client = APIClient()
    response = client.get("/ipif/statements/")
    assert response.data == [StatementSerializer(statement).data]

    response = client.get("/testrepo/ipif/statements/")
    assert response.data == [StatementSerializer(statement).data]


@pytest.mark.django_db(transaction=True)
def test_request_for_specific_statements(statement, factoid):
    client = APIClient()
    response = client.get("/ipif/statements/http://test.com/statement/statement1")
    assert response.data == StatementSerializer(statement).data

    response = client.get("/testrepo/ipif/statements/statement1")
    assert response.data == StatementSerializer(statement).data


@pytest.mark.django_db(transaction=True)
def test_request_for_sources(source, factoid):
    client = APIClient()
    response = client.get("/ipif/sources/")
    assert response.data == [SourceSerializer(source).data]

    response = client.get("/testrepo/ipif/sources/")
    assert response.data == [SourceSerializer(source).data]


@pytest.mark.django_db(transaction=True)
def test_request_for_specific_sources(source, factoid):
    client = APIClient()
    response = client.get("/ipif/sources/http://test.com/source/source1")
    assert response.data == SourceSerializer(source).data

    response = client.get("/testrepo/ipif/sources/source1")
    assert response.data == SourceSerializer(source).data


@pytest.mark.django_db(transaction=True)
def test_request_for_factoids(factoid):
    client = APIClient()
    response = client.get("/ipif/factoids/")
    assert response.data == [FactoidSerializer(factoid).data]

    response = client.get("/testrepo/ipif/factoids/")
    assert response.data == [FactoidSerializer(factoid).data]


@pytest.mark.django_db(transaction=True)
def test_request_for_specific_factoids(factoid):
    client = APIClient()
    response = client.get("/ipif/factoids/http://test.com/factoid/factoid1")
    assert response.data == FactoidSerializer(factoid).data

    response = client.get("/testrepo/ipif/factoids/factoid1")
    assert response.data == FactoidSerializer(factoid).data
