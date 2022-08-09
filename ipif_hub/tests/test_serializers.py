import pytest

from ipif_hub.models import IpifRepo, Person, Source, Statement, Factoid
from ipif_hub.serializers import (
    PersonRefSerializer,
    SourceRefSerializer,
    StatementRefSerializer,
    FactoidRefSerializer,
)

from ipif_hub.tests.conftest import person, source, statement, factoid


@pytest.mark.django_db
def test_person_ref_serializer(person):
    serialized_data = PersonRefSerializer(person).data
    assert serialized_data.get("@id") == "http://test.com/persons/person1"
    assert serialized_data.get("label") == "Person One"


@pytest.mark.django_db
def test_source_ref_serializer(source):
    serialized_data = SourceRefSerializer(source).data
    assert serialized_data.get("@id") == "http://test.com/sources/source1"
    assert serialized_data.get("label") == "Source One"


@pytest.mark.django_db
def test_source_ref_serializer(statement):
    serialized_data = StatementRefSerializer(statement).data
    assert serialized_data.get("@id") == "http://test.com/statements/statement1"
    assert serialized_data.get("label") == "Statement One"


@pytest.mark.django_db(transaction=True)
def test_source_ref_serializer(factoid, person, statement, source):
    serialized_data = FactoidRefSerializer(factoid).data
    assert serialized_data.get("@id") == "http://test.com/factoids/factoid1"
    assert serialized_data.get("label") == "Factoid One"
