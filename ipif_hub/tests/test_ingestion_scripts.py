from copy import deepcopy
import datetime
import pytest

from ipif_hub.models import IpifRepo, Person, Source, URI
from ipif_hub.management.utils.ingest_data import (
    DataFormatError,
    ingest_person_or_source,
)

from ipif_hub.tests.conftest import repo

"""
TEST PERSON INGESTION
"""


@pytest.fixture
def person1_data():
    data = {
        "@id": "Person1",
        "label": "Person Number One",
        "uris": ["http://other.com/person1"],
        "createdBy": "Researcher1",
        "createdWhen": "2012-04-23",
        "modifiedBy": "Researcher1",
        "modifiedWhen": "2012-04-23",
    }
    return data


@pytest.fixture
def person1_data_update():
    data = {
        "@id": "Person1",
        "label": "Person Number One",
        "uris": ["http://changed.com/person1"],
        "createdBy": "Researcher1",
        "createdWhen": "2012-04-23",
        "modifiedBy": "Researcher2",
        "modifiedWhen": "2015-04-23",
    }

    return data


@pytest.fixture
def person1_data_error():
    data = {
        "label": "Person Number One",
        "uris": ["http://other.com/person1"],
        "createdBy": "Researcher1",
        "createdWhen": "2012-04-23",
        "modifiedBy": "Researcher1",
        "modifiedWhen": "2012-04-23",
    }
    return data


@pytest.mark.django_db(transaction=True)
def test_ingest_person_with_valid_data(repo: IpifRepo, person1_data: dict):
    ingest_person_or_source(Person, person1_data, repo)

    p: Person = Person.objects.get(pk="http://test.com/persons/Person1")
    assert p
    assert p.uris.first().uri == "http://other.com/person1"
    assert p.local_id == "Person1"
    assert p.createdBy == "Researcher1"
    assert p.createdWhen == datetime.date(2012, 4, 23)
    assert p.modifiedBy == "Researcher1"
    assert p.modifiedWhen == datetime.date(2012, 4, 23)


@pytest.mark.django_db(transaction=True)
def test_ingest_person_with_invalid_data(repo: IpifRepo, person1_data_error):

    with pytest.raises(DataFormatError) as e:
        ingest_person_or_source(Person, person1_data_error, repo)
    assert "'@id' is a required property" in str(e.value)


@pytest.mark.django_db(transaction=True)
def test_ingest_person_with_updated_data(
    repo: IpifRepo,
    person1_data: dict,
    person1_data_update: dict,
):

    # Ingest original
    ingest_person_or_source(
        Person,
        person1_data,
        repo,
    )

    # Ingest update
    ingest_person_or_source(
        Person,
        person1_data_update,
        repo,
    )

    p: Person = Person.objects.get(pk="http://test.com/persons/Person1")

    assert p
    assert p.uris.first().uri == "http://changed.com/person1"
    assert p.local_id == "Person1"
    assert p.createdBy == "Researcher1"
    assert p.createdWhen == datetime.date(2012, 4, 23)
    assert p.modifiedBy == "Researcher2"
    assert p.modifiedWhen == datetime.date(2015, 4, 23)

    # Check the URI has been replaced, not added to
    assert len(p.uris.all()) == 1


"""
TEST SOURCE INGESTION
"""


@pytest.fixture
def source1_data():
    data = {
        "@id": "Source1",
        "label": "Source Number One",
        "uris": ["http://other.com/source1"],
        "createdBy": "Researcher1",
        "createdWhen": "2012-04-23",
        "modifiedBy": "Researcher1",
        "modifiedWhen": "2012-04-23",
    }
    return data


@pytest.fixture
def source1_data_update():
    data = {
        "@id": "Source1",
        "label": "Source Number One",
        "uris": ["http://changed.com/source1"],
        "createdBy": "Researcher1",
        "createdWhen": "2012-04-23",
        "modifiedBy": "Researcher2",
        "modifiedWhen": "2015-04-23",
    }

    return data


@pytest.fixture
def source1_data_error():
    data = {
        "label": "Source Number One",
        "uris": ["http://other.com/source1"],
        "createdBy": "Researcher1",
        "createdWhen": "2012-04-23",
        "modifiedBy": "Researcher1",
        "modifiedWhen": "2012-04-23",
    }
    return data


@pytest.mark.django_db(transaction=True)
def test_ingest_source_with_valid_data(repo: IpifRepo, source1_data: dict):
    ingest_person_or_source(Source, source1_data, repo)

    p: Source = Source.objects.get(pk="http://test.com/sources/Source1")
    assert p
    assert p.uris.first().uri == "http://other.com/source1"
    assert p.local_id == "Source1"
    assert p.createdBy == "Researcher1"
    assert p.createdWhen == datetime.date(2012, 4, 23)
    assert p.modifiedBy == "Researcher1"
    assert p.modifiedWhen == datetime.date(2012, 4, 23)


@pytest.mark.django_db(transaction=True)
def test_ingest_source_with_invalid_data(repo: IpifRepo, source1_data_error):

    with pytest.raises(DataFormatError) as e:
        ingest_person_or_source(Source, source1_data_error, repo)
    assert "'@id' is a required property" in str(e.value)


@pytest.mark.django_db(transaction=True)
def test_ingest_source_with_updated_data(
    repo: IpifRepo,
    source1_data: dict,
    source1_data_update: dict,
):

    # Ingest original
    ingest_person_or_source(
        Source,
        source1_data,
        repo,
    )

    # Ingest update
    ingest_person_or_source(
        Source,
        source1_data_update,
        repo,
    )

    p: Source = Source.objects.get(pk="http://test.com/sources/Source1")

    assert p
    assert p.uris.first().uri == "http://changed.com/source1"
    assert p.local_id == "Source1"
    assert p.createdBy == "Researcher1"
    assert p.createdWhen == datetime.date(2012, 4, 23)
    assert p.modifiedBy == "Researcher2"
    assert p.modifiedWhen == datetime.date(2015, 4, 23)

    # Check the URI has been replaced, not added to
    assert len(p.uris.all()) == 1
