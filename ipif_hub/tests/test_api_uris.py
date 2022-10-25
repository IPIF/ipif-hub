import pytest
from rest_framework.test import APIClient

from ipif_hub.models import Factoid, IpifRepo, Person, Source, Statement
from ipif_hub.serializers import (
    FactoidSerializer,
    MergePersonSerializer,
    MergeSourceSerializer,
    PersonSerializer,
    SourceSerializer,
    StatementSerializer,
)


@pytest.mark.django_db(transaction=True)
def test_request_for_persons(person, factoid):
    client = APIClient()
    response = client.get("/ipif/persons/")
    assert response.data == [MergePersonSerializer(person.merge_person.first()).data]

    response = client.get("/testrepo/ipif/persons/")
    assert response.data == [PersonSerializer(person).data]


def test_request_for_specific_persons(transactional_db, person, factoid):

    client = APIClient()
    response = client.get("/ipif/persons/http://test.com/persons/person1")
    assert response.data == MergePersonSerializer(person.merge_person.first()).data

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
    assert response.data == [MergeSourceSerializer(source.merge_source.first()).data]

    response = client.get("/testrepo/ipif/sources/")
    assert response.data == [SourceSerializer(source).data]


@pytest.mark.django_db(transaction=True)
def test_request_for_specific_sources(source, factoid):
    client = APIClient()
    response = client.get("/ipif/sources/http://test.com/source/source1")
    assert response.data == MergeSourceSerializer(source.merge_source.first()).data

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


@pytest.mark.django_db(transaction=True)
def test_request_post_data(repo: IpifRepo):
    client = APIClient()
    response = client.post(
        f"/{repo.endpoint_slug}/ipif/persons/",
        data=[
            {
                "@id": "Person1",
                "label": "Person Number One",
                "uris": [
                    "http://ahpiss.com/Person1",
                    "http://gnd.de/Person1",
                    "http://shouldbethere.com",
                ],
                "createdBy": "Researcher3",
                "createdWhen": "2012-04-23",
                "modifiedBy": "Researcher4",
                "modifiedWhen": "2012-04-23",
            }
        ],
        format="json",
    )
    assert response.status_code == 200
    assert (
        "Creating <Person @id=http://test.com/persons/Person1>"
        in response.data["detail"]
    )

    response = client.get(f"/{repo.endpoint_slug}/ipif/persons/Person1")
    assert response.status_code == 200
    assert response.data == PersonSerializer(Person.objects.first()).data

    response = client.post(
        f"/{repo.endpoint_slug}/ipif/sources/",
        data=[
            {
                "@id": "Source1",
                "label": "Source Number One (Smith, 1900)",
                "uris": ["http://books.net/s1", "http://whsmith.com/sno"],
                "createdBy": "Researcher1",
                "createdWhen": "2012-04-23",
                "modifiedBy": "Researcher1",
                "modifiedWhen": "2012-04-23",
            }
        ],
        format="json",
    )
    assert response.status_code == 200
    assert (
        "Creating <Source @id=http://test.com/sources/Source1>"
        in response.data["detail"]
    )
    response = client.get(f"/{repo.endpoint_slug}/ipif/sources/Source1")
    assert response.status_code == 200
    assert response.data == SourceSerializer(Source.objects.first()).data

    response = client.post(
        f"/{repo.endpoint_slug}/ipif/statements/",
        data=[
            {
                "@id": "St1-John-Smith-Name",
                "places": [],
                "createdBy": "RHadden",
                "createdWhen": "2022-03-25",
                "modifiedBy": "RHadden",
                "modifiedWhen": "2022-03-25",
                "label": "",
                "statementType": {
                    "uri": "http://vocabs.com/hasName",
                    "label": "Has Name",
                },
                "name": "John Smith",
            },
            {
                "@id": "St2-jsmith-teacher",
                "places": [{"uri": "http://places.com/Germany", "label": "Germany"}],
                "createdBy": "RHadden",
                "createdWhen": "2022-03-25",
                "modifiedBy": "RHadden",
                "modifiedWhen": "2022-03-25",
                "label": "",
                "role": {"label": "teachery", "uri": "http://jobs.com/teacher"},
                "relatesToPerson": [
                    {"uri": "http://persons.com/mrsSpenceley", "label": "Mrs Spenceley"}
                ],
            },
        ],
        format="json",
    )
    assert response.status_code == 200
    assert (
        "Creating <Statement @id=http://test.com/statements/St1-John-Smith-Name>"
        in response.data["detail"]
    )
    assert (
        "Creating <Statement @id=http://test.com/statements/St2-jsmith-teacher>"
        in response.data["detail"]
    )

    response = client.get(f"/{repo.endpoint_slug}/ipif/statements/St1-John-Smith-Name")
    assert response.status_code == 200
    assert (
        response.data
        == StatementSerializer(
            Statement.objects.filter(local_id="St1-John-Smith-Name").first()
        ).data
    )

    response = client.post(
        f"/{repo.endpoint_slug}/ipif/factoids/",
        data=[
            {
                "@id": "Factoid1",
                "person-ref": {"@id": "Person1"},
                "source-ref": {"@id": "Source1"},
                "statement-refs": [
                    {"@id": "St1-John-Smith-Name"},
                    {"@id": "St2-jsmith-teacher"},
                ],
                "createdBy": "Researcher4",
                "createdWhen": "2012-04-23",
                "modifiedBy": "Researcher2",
                "modifiedWhen": "2012-04-23",
            }
        ],
        format="json",
    )
    assert response.status_code == 200
    assert (
        "Creating <Factoid @id=http://test.com/factoids/Factoid1>"
        in response.data["detail"]
    )

    response = client.get(f"/{repo.endpoint_slug}/ipif/factoids/Factoid1")
    assert response.status_code == 200
    assert response.data == FactoidSerializer(Factoid.objects.first()).data
