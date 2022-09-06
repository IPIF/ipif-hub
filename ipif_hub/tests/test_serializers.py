import datetime

import pytest

from ipif_hub.models import MergePerson, MergeSource
from ipif_hub.serializers import (
    FactoidRefSerializer,
    FactoidSerializer,
    MergePersonSerializer,
    MergeSourceSerializer,
    PersonRefSerializer,
    PersonSerializer,
    PlaceSerializer,
    SourceRefSerializer,
    SourceSerializer,
    StatementRefSerializer,
    StatementSerializer,
    URISerlializer,
)
from ipif_hub.tests.conftest import created_modified


@pytest.mark.django_db(transaction=True)
def test_uri_serializer(uri):
    assert URISerlializer(uri).data == {"uri": "http://person_uri.com/person1"}


@pytest.mark.django_db(transaction=True)
def test_place_serializer(place):
    assert PlaceSerializer(place).data == {
        "uri": "http://places.com/place1",
        "label": "place1",
    }


@pytest.mark.django_db(transaction=True)
def test_person_ref_serializer(person):
    assert PersonRefSerializer(person).data == {
        "@id": "http://test.com/persons/person1",
        "label": "Person One",
    }


@pytest.mark.django_db(transaction=True)
def test_source_ref_serializer(source):
    serialized_data = SourceRefSerializer(source).data
    assert serialized_data.get("@id") == "http://test.com/sources/source1"
    assert serialized_data.get("label") == "Source One"


@pytest.mark.django_db
def test_statetment_ref_serializer(statement):
    serialized_data = StatementRefSerializer(statement).data
    assert serialized_data.get("@id") == "http://test.com/statements/statement1"
    assert serialized_data.get("label") == "Statement One"


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
def test_factoid_ref_serializer(factoid, person, statement, source):
    serialized_data = FactoidRefSerializer(factoid).data
    assert serialized_data.get("@id") == "http://test.com/factoids/factoid1"
    assert serialized_data.get("label") == "Factoid One"


@pytest.mark.django_db(transaction=True)
def test_person_serializer(person, factoid):
    serialized_data = PersonSerializer(person).data
    assert serialized_data.get("@id") == "http://test.com/persons/person1"
    assert serialized_data.get("label") == "Person One"
    assert serialized_data.get("uris") == ["http://alternative.com/person1"]
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
        serialized_data.get("relatesToPerson")[0]["uri"] == "http://related.com/person1"
    )
    assert serialized_data.get("relatesToPerson")[0]["label"] == "Related Person"
    assert serialized_data.get("places")[0]["uri"] == "http://places.com/nowhere"
    assert serialized_data.get("places")[0]["label"] == "Nowhere"


@pytest.mark.django_db(transaction=True)
def test_factoid_serializer(factoid):
    serialized_data = FactoidSerializer(factoid).data
    assert serialized_data.get("@id") == "http://test.com/factoids/factoid1"
    assert serialized_data.get("label") == "Factoid One"
    verify_created_modified(serialized_data)

    assert serialized_data.get("person-ref")["@id"] == "http://test.com/persons/person1"
    assert serialized_data.get("person-ref")["label"] == "Person One"
    assert serialized_data.get("source-ref")["@id"] == "http://test.com/sources/source1"
    assert serialized_data.get("source-ref")["label"] == "Source One"
    assert (
        serialized_data.get("statement-refs")[0]["@id"]
        == "http://test.com/statements/statement1"
    )
    assert serialized_data.get("statement-refs")[0]["label"] == "Statement One"


@pytest.mark.django_db(transaction=True)
def test_merge_person_serializer(
    factoid,
    factoid2,
    factoid3,
    source,
    statement,
    repo,
    person,
    person_sameAs,
):

    # TODO: It's really dumb that we're not really decoupling the automatic
    # creation of the object from testing the serializer
    assert len(MergePerson.objects.all()) == 1

    merge_person = MergePerson.objects.first()

    serialized_data = MergePersonSerializer(merge_person).data

    # ID regenerates each time: could mock this to be stable,
    # but it's really fine so just don't bother
    serialized_data.pop("@id")

    assert serialized_data == {
        "createdBy": "ipif-hub",
        "createdWhen": str(datetime.date.today()),
        "modifiedBy": "ipif-hub",
        "modifiedWhen": str(datetime.date.today()),
        "uris": ["http://alternative.com/person1"],
        "factoid-refs": [
            {
                "@id": "http://test.com/factoids/factoid1",
                "label": "Factoid One",
                "person-ref": {
                    "@id": "http://test.com/persons/person1",
                    "label": "Person One",
                },
                "source-ref": {
                    "@id": "http://test.com/sources/source1",
                    "label": "Source One",
                },
                "statement-refs": [
                    {
                        "@id": "http://test.com/statements/statement1",
                        "label": "Statement One",
                    }
                ],
            },
            {
                "@id": "http://test.com/factoids/factoid2",
                "label": "Factoid Two",
                "person-ref": {
                    "@id": "http://test.com/persons/person1",
                    "label": "Person One",
                },
                "source-ref": {
                    "@id": "http://test.com/sources/source1",
                    "label": "Source One",
                },
                "statement-refs": [
                    {
                        "@id": "http://test.com/statements/statement2",
                        "label": "Statement Two",
                    }
                ],
            },
            {
                "@id": "http://test.com/factoids/factoid3",
                "label": "Factoid Three",
                "person-ref": {
                    "@id": "http://test2.com/persons/person_sameAs",
                    "label": "Person SameAs",
                },
                "source-ref": {
                    "@id": "http://test.com/sources/source1",
                    "label": "Source One",
                },
                "statement-refs": [
                    {
                        "@id": "http://test.com/statements/statement2",
                        "label": "Statement Two",
                    }
                ],
            },
        ],
    }


@pytest.mark.django_db(transaction=True)
def test_merge_source_serializer(
    factoid,
    factoid2,
    factoid3,
    source,
    sourceSameAs,
    statement,
    repo,
    person,
):

    merge_source: MergeSource = MergeSource(
        createdBy="ipif-hub",
        createdWhen=datetime.date.today(),
        modifiedBy="ipif-hub",
        modifiedWhen=datetime.date.today(),
    )
    merge_source.save()
    merge_source.sources.add(source, sourceSameAs)

    serialized_data = MergeSourceSerializer(merge_source).data

    # ID regenerates each time: could mock this to be stable,
    # but it's really fine so just don't bother
    serialized_data.pop("@id")

    # No guaranteed order for returning these!
    uris = set(serialized_data.pop("uris"))
    assert uris == set(
        ["http://sources.com/source1", "http://sources.com/sourceSameAs"]
    )

    assert serialized_data == {
        "createdBy": "ipif-hub",
        "createdWhen": str(datetime.date.today()),
        "modifiedBy": "ipif-hub",
        "modifiedWhen": str(datetime.date.today()),
        "factoid-refs": [
            {
                "@id": "http://test.com/factoids/factoid1",
                "label": "Factoid One",
                "person-ref": {
                    "@id": "http://test.com/persons/person1",
                    "label": "Person One",
                },
                "source-ref": {
                    "@id": "http://test.com/sources/source1",
                    "label": "Source One",
                },
                "statement-refs": [
                    {
                        "@id": "http://test.com/statements/statement1",
                        "label": "Statement One",
                    }
                ],
            },
            {
                "@id": "http://test.com/factoids/factoid2",
                "label": "Factoid Two",
                "person-ref": {
                    "@id": "http://test.com/persons/person1",
                    "label": "Person One",
                },
                "source-ref": {
                    "@id": "http://test.com/sources/source1",
                    "label": "Source One",
                },
                "statement-refs": [
                    {
                        "@id": "http://test.com/statements/statement2",
                        "label": "Statement Two",
                    }
                ],
            },
            {
                "@id": "http://test.com/factoids/factoid3",
                "label": "Factoid Three",
                "person-ref": {
                    "@id": "http://test2.com/persons/person_sameAs",
                    "label": "Person SameAs",
                },
                "source-ref": {
                    "@id": "http://test.com/sources/source1",
                    "label": "Source One",
                },
                "statement-refs": [
                    {
                        "@id": "http://test.com/statements/statement2",
                        "label": "Statement Two",
                    }
                ],
            },
        ],
    }
