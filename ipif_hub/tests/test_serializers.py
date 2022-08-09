import pytest

from ipif_hub.models import IpifRepo, Person, Source, Statement, Factoid
from ipif_hub.serializers import (
    PersonRefSerializer,
    SourceRefSerializer,
    StatementRefSerializer,
    FactoidRefSerializer,
    PersonSerializer,
    SourceSerializer,
    StatementSerializer,
    FactoidSerializer,
)

from ipif_hub.tests.conftest import person, source, statement, factoid, created_modified


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
def test_statetment_ref_serializer(statement):
    serialized_data = StatementRefSerializer(statement).data
    assert serialized_data.get("@id") == "http://test.com/statements/statement1"
    assert serialized_data.get("label") == "Statement One"


@pytest.mark.django_db(transaction=True)
def test_factoid_ref_serializer(factoid, person, statement, source):
    serialized_data = FactoidRefSerializer(factoid).data
    assert serialized_data.get("@id") == "http://test.com/factoids/factoid1"
    assert serialized_data.get("label") == "Factoid One"


def verify_created_modified(serialized_data):
    """Checks created/modified fields are correct (call from other tests)"""

    assert serialized_data.get("createdBy") == created_modified["createdBy"]
    assert serialized_data.get("createdWhen") == str(created_modified["createdWhen"])
    assert serialized_data.get("modifiedBy") == created_modified["modifiedBy"]
    assert serialized_data.get("modifiedWhen") == str(created_modified["modifiedWhen"])


def verify_associated_factoid_ref(serialized_data):
    factoid_refs = serialized_data.get("factoid-refs")
    assert factoid_refs
    assert factoid_refs[0]["source-ref"]["@id"] == "http://test.com/sources/source1"
    assert factoid_refs[0]["person-ref"]["@id"] == "http://test.com/persons/person1"
    assert (
        factoid_refs[0]["statement-refs"][0]["@id"]
        == "http://test.com/statements/statement1"
    )


@pytest.mark.django_db(transaction=True)
def test_person_serializer(person, factoid):
    serialized_data = PersonSerializer(person).data
    assert serialized_data.get("@id") == "http://test.com/persons/person1"
    assert serialized_data.get("label") == "Person One"
    verify_created_modified(serialized_data)
    verify_associated_factoid_ref(serialized_data)


@pytest.mark.django_db(transaction=True)
def test_source_serializer(source, factoid):
    serialized_data = SourceSerializer(source).data
    assert serialized_data.get("@id") == "http://test.com/sources/source1"
    assert serialized_data.get("label") == "Source One"
    verify_created_modified(serialized_data)
    verify_associated_factoid_ref(serialized_data)


@pytest.mark.django_db(transaction=True)
def test_statement_serializer(statement, factoid):
    serialized_data = StatementSerializer(statement).data
    assert serialized_data.get("@id") == "http://test.com/statements/statement1"
    assert serialized_data.get("label") == "Statement One"
    verify_created_modified(serialized_data)
    verify_associated_factoid_ref(serialized_data)

    assert (
        serialized_data.get("statementType")["uri"]
        == "http://all_purpose_statement.com"
    )
    assert serialized_data.get("statementType")["label"] == "All Purpose Statement"
    assert serialized_data.get("name") == "John Smith"
    assert serialized_data.get("role")["uri"] == "http://role.com/unemployed"
    assert serialized_data.get("role")["label"] == "unemployed"
    assert serialized_data.get("date")["sortdate"] == "1900-01-01"
    assert serialized_data.get("date")["label"] == "1 Jan 1900"
    assert serialized_data.get("memberOf")["uri"] == "http://orgs.com/madeup"
    assert serialized_data.get("memberOf")["label"] == "Made Up Organisation"
    assert serialized_data.get("statementText") == "John Smith is a Member of Madeup"
    assert (
        serialized_data.get("relatesToPerson")[0]["uri"]
        == "http://test.com/persons/related_person"
    )
    assert serialized_data.get("relatesToPerson")[0]["label"] == "Related Person"
    assert serialized_data.get("places")[0]["uri"] == "http://places.com/nowhere"
    assert serialized_data.get("places")[0]["label"] == "Nowhere"
