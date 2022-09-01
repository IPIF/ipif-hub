import datetime

import pytest

from ipif_hub.management.utils.ingest_data import (
    NO_CHANGE_TO_DATA,
    DataFormatError,
    DataIntegrityError,
    ingest_data,
    ingest_factoid,
    ingest_person_or_source,
    ingest_statement,
)
from ipif_hub.models import (
    Factoid,
    IpifRepo,
    Person,
    Source,
    Statement,
    get_ipif_hub_repo_AUTOCREATED_instance,
)


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


person1_data_duplicate = person1_data


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


@pytest.mark.django_db
def test_ingest_person_with_valid_data(repo: IpifRepo, person1_data: dict):
    ingest_person_or_source(Person, person1_data, repo)

    p: Person = Person.objects.get(identifier="http://test.com/persons/Person1")
    assert p
    assert p.uris
    # assert p.uris.filter(uri="http://test.com/persons/Person1")
    assert p.uris.filter(uri="http://other.com/person1")
    assert p.local_id == "Person1"
    assert p.createdBy == "Researcher1"
    assert p.createdWhen == datetime.date(2012, 4, 23)
    assert p.modifiedBy == "Researcher1"
    assert p.modifiedWhen == datetime.date(2012, 4, 23)


@pytest.mark.django_db
def test_ingest_person_with_same_data_returns_no_change(
    repo: IpifRepo,
    person1_data: dict,
    person1_data_duplicate,
):
    ingest_person_or_source(Person, person1_data, repo)
    assert (
        ingest_person_or_source(Person, person1_data_duplicate, repo)
        == NO_CHANGE_TO_DATA
    )


@pytest.mark.django_db
def test_ingest_person_with_invalid_data(repo: IpifRepo, person1_data_error):

    with pytest.raises(DataFormatError) as e:
        ingest_person_or_source(Person, person1_data_error, repo)
    assert "'@id' is a required property" in str(e.value)


@pytest.mark.django_db
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

    p: Person = Person.objects.get(identifier="http://test.com/persons/Person1")

    assert p
    assert p.uris.filter(uri="http://changed.com/person1")
    # assert p.uris.filter(uri="http://test.com/persons/Person1")
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


source1_data_duplicate = source1_data


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


@pytest.mark.django_db
def test_ingest_source_with_valid_data(repo: IpifRepo, source1_data: dict):
    ingest_person_or_source(Source, source1_data, repo)

    p: Source = Source.objects.get(identifier="http://test.com/sources/Source1")
    assert p
    assert p.uris.filter(uri="http://other.com/source1")
    # assert p.uris.filter(uri="http://test.com/sources/Source1")
    assert p.local_id == "Source1"
    assert p.createdBy == "Researcher1"
    assert p.createdWhen == datetime.date(2012, 4, 23)
    assert p.modifiedBy == "Researcher1"
    assert p.modifiedWhen == datetime.date(2012, 4, 23)


@pytest.mark.django_db
def test_ingest_source_with_same_data_returns_no_change(
    repo: IpifRepo,
    source1_data: dict,
    source1_data_duplicate,
):
    ingest_person_or_source(Source, source1_data, repo)
    assert (
        ingest_person_or_source(Source, source1_data_duplicate, repo)
        == NO_CHANGE_TO_DATA
    )


@pytest.mark.django_db
def test_ingest_source_with_invalid_data(repo: IpifRepo, source1_data_error):

    with pytest.raises(DataFormatError) as e:
        ingest_person_or_source(Source, source1_data_error, repo)
    assert "'@id' is a required property" in str(e.value)


@pytest.mark.django_db
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

    p: Source = Source.objects.get(identifier="http://test.com/sources/Source1")

    assert p
    assert p.uris.filter(uri="http://changed.com/source1")
    # assert p.uris.filter(uri="http://test.com/sources/Source1")
    assert p.local_id == "Source1"
    assert p.createdBy == "Researcher1"
    assert p.createdWhen == datetime.date(2012, 4, 23)
    assert p.modifiedBy == "Researcher2"
    assert p.modifiedWhen == datetime.date(2015, 4, 23)

    # Check the URI has been replaced, not added to
    assert len(p.uris.all()) == 1


@pytest.fixture
def statement1_data():
    data = {
        "@id": "St1-John-Smith-Name",
        "places": [
            {
                "uri": "http://places.com/Gibraltar",
                "label": "Gibraltar",
            },
        ],
        "createdBy": "Researcher1",
        "createdWhen": "2022-03-25",
        "modifiedBy": "Researcher1",
        "modifiedWhen": "2022-03-25",
        "label": "John Smith is called John Smith",
        "statementType": {
            "uri": "http://vocabs.com/hasName",
            "label": "Has Name",
        },
        "name": "John Smith",
    }

    return data


statement1_data_duplicate = statement1_data


@pytest.fixture
def statement1_data_error():
    data = {
        "places": [
            {
                "uri": "http://places.com/Gibraltar",
                "label": "Gibraltar",
            },
        ],
        "createdBy": "Researcher1",
        "createdWhen": "2022-03-25",
        "modifiedBy": "Researcher1",
        "modifiedWhen": "2022-03-25",
        "label": "John Smith is called John Smith",
        "statementType": {
            "uri": "http://vocabs.com/hasName",
            "label": "Has Name",
        },
        "name": "John Smith",
    }

    return data


@pytest.mark.django_db
def test_statement_ingestion_with_valid_data(repo: IpifRepo, statement1_data: dict):
    ingest_statement(statement1_data, repo)

    st: Statement = Statement.objects.get(
        identifier="http://test.com/statements/St1-John-Smith-Name"
    )
    assert st.local_id == "St1-John-Smith-Name"
    assert st.label == "John Smith is called John Smith"
    assert st.createdBy == "Researcher1"
    assert st.createdWhen == datetime.date(2022, 3, 25)
    assert st.modifiedBy == "Researcher1"
    assert st.modifiedWhen == datetime.date(2022, 3, 25)
    assert st.places.first().uri == "http://places.com/Gibraltar"
    assert st.name == "John Smith"
    assert st.statementType_uri == "http://vocabs.com/hasName"
    assert st.statementType_label == "Has Name"


@pytest.mark.django_db
def test_ingest_statement_with_same_data_returns_no_change(
    repo: IpifRepo,
    statement1_data: dict,
    statement1_data_duplicate,
):
    ingest_statement(statement1_data, repo)
    assert ingest_statement(statement1_data_duplicate, repo) == NO_CHANGE_TO_DATA


@pytest.mark.django_db
def test_statement_ingestion_with_invalid_data(
    repo: IpifRepo, statement1_data_error: dict
):

    with pytest.raises(DataFormatError) as e:
        ingest_statement(statement1_data_error, repo)
    assert "'@id' is a required property" in str(e.value)


@pytest.fixture
def statement1_data_update():
    data = {
        "@id": "St1-John-Smith-Name",
        "places": [
            {
                "uri": "http://places.com/France",
                "label": "France",
            },
        ],
        "createdBy": "Researcher1",
        "createdWhen": "2022-03-25",
        "modifiedBy": "Researcher2",
        "modifiedWhen": "2022-04-25",
        "label": "John Smith is called John Smuth",
        "statementType": {
            "uri": "http://vocabs.com/hasName",
            "label": "Has Name",
        },
        "name": "John Smuth",
    }

    return data


@pytest.mark.django_db
def test_statement_ingestion_with_updated_data(
    repo: IpifRepo, statement1_data: dict, statement1_data_update: dict
):
    ingest_statement(statement1_data, repo)

    ingest_statement(statement1_data_update, repo)

    st: Statement = Statement.objects.get(
        identifier="http://test.com/statements/St1-John-Smith-Name"
    )
    assert st.local_id == "St1-John-Smith-Name"
    assert st.label == "John Smith is called John Smuth"
    assert st.createdBy == "Researcher1"
    assert st.createdWhen == datetime.date(2022, 3, 25)
    assert st.modifiedBy == "Researcher2"
    assert st.modifiedWhen == datetime.date(2022, 4, 25)
    assert st.places.first().uri == "http://places.com/France"
    assert st.name == "John Smuth"
    assert st.statementType_uri == "http://vocabs.com/hasName"
    assert st.statementType_label == "Has Name"


@pytest.fixture
def factoid1_data():
    data = {
        "@id": "Factoid1",
        "person-ref": {"@id": "Person1"},
        "source-ref": {"@id": "Source1"},
        "statement-refs": [
            {"@id": "St1-John-Smith-Name"},
        ],
        "createdBy": "Researcher1",
        "createdWhen": "2012-04-23",
        "modifiedBy": "Researcher1",
        "modifiedWhen": "2012-04-23",
    }
    return data


factoid1_data_duplicate = factoid1_data


@pytest.mark.django_db
def test_ingest_factoid_with_valid_data_and_refs_already_created(
    repo: IpifRepo,
    factoid1_data: dict,
    person1_data: dict,
    source1_data: dict,
    statement1_data: dict,
):
    ingest_person_or_source(Person, person1_data, repo)
    ingest_person_or_source(Source, source1_data, repo)
    ingest_statement(statement1_data, repo)
    ingest_factoid(factoid1_data, repo)

    f: Factoid = Factoid.objects.get(identifier="http://test.com/factoids/Factoid1")
    assert f.local_id == "Factoid1"
    assert f.createdBy == "Researcher1"
    assert f.createdWhen == datetime.date(2012, 4, 23)
    assert f.modifiedBy == "Researcher1"
    assert f.modifiedWhen == datetime.date(2012, 4, 23)

    assert f.person == Person.objects.get(identifier="http://test.com/persons/Person1")
    assert f.source == Source.objects.get(identifier="http://test.com/sources/Source1")
    assert (
        Statement.objects.get(
            identifier="http://test.com/statements/St1-John-Smith-Name"
        )
        in f.statements.all()
    )


@pytest.mark.django_db
def test_ingest_factoid_with_same_data_returns_no_change(
    repo: IpifRepo,
    factoid1_data: dict,
    factoid1_data_duplicate: dict,
    person1_data: dict,
    source1_data: dict,
    statement1_data: dict,
):
    ingest_person_or_source(Person, person1_data, repo)
    ingest_person_or_source(Source, source1_data, repo)
    ingest_statement(statement1_data, repo)
    ingest_factoid(factoid1_data, repo)

    assert ingest_factoid(factoid1_data_duplicate, repo) == NO_CHANGE_TO_DATA


@pytest.mark.django_db
def test_ingest_factoid_fails_with_missing_person_ref(
    repo: IpifRepo,
    factoid1_data: dict,
    person1_data: dict,
    source1_data: dict,
    statement1_data: dict,
):
    # ingest_person_or_source(Person, person1_data, repo)
    ingest_person_or_source(Source, source1_data, repo)
    ingest_statement(statement1_data, repo)

    with pytest.raises(DataIntegrityError) as e:
        ingest_factoid(factoid1_data, repo)


@pytest.mark.django_db
def test_ingest_factoid_fails_with_missing_source_ref(
    repo: IpifRepo,
    factoid1_data: dict,
    person1_data: dict,
    source1_data: dict,
    statement1_data: dict,
):
    # ingest_person_or_source(Person, person1_data, repo)
    ingest_person_or_source(Source, source1_data, repo)
    # ingest_statement(statement1_data, repo)

    with pytest.raises(DataIntegrityError) as e:
        ingest_factoid(factoid1_data, repo)


@pytest.mark.django_db
def test_ingest_factoid_fails_with_missing_statement_ref(
    repo: IpifRepo,
    factoid1_data: dict,
    person1_data: dict,
    source1_data: dict,
    statement1_data: dict,
):
    ingest_person_or_source(Person, person1_data, repo)
    ingest_person_or_source(Source, source1_data, repo)
    # ingest_statement(statement1_data, repo)

    with pytest.raises(DataIntegrityError) as e:
        ingest_factoid(factoid1_data, repo)


@pytest.fixture
def factoid1_data_update():
    data = {
        "@id": "Factoid1",
        "person-ref": {"@id": "Person1"},
        "source-ref": {"@id": "Source1"},
        "statement-refs": [
            {"@id": "St1-John-Smith-Name"},
            {"@id": "St2-jsmith-teacher"},
        ],
        "createdBy": "Researcher1",
        "createdWhen": "2012-04-23",
        "modifiedBy": "Researcher2",
        "modifiedWhen": "2012-04-24",
    }
    return data


@pytest.fixture
def factoid1_data_error():
    data = {
        "person-ref": {"@id": "Person1"},
        "source-ref": {"@id": "Source1"},
        "statement-refs": [
            {"@id": "St1-John-Smith-Name"},
            {"@id": "St2-jsmith-teacher"},
        ],
        "createdBy": "Researcher1",
        "createdWhen": "2012-04-23",
        "modifiedBy": "Researcher2",
        "modifiedWhen": "2012-04-24",
    }
    return data


@pytest.fixture
def statement2_data():
    data = {
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
    }
    return data


@pytest.mark.django_db
def test_ingest_factoid_with_updated_data(
    repo: IpifRepo,
    factoid1_data: dict,
    person1_data: dict,
    source1_data: dict,
    statement1_data: dict,
    factoid1_data_update: dict,
    statement2_data: dict,
):
    AUTOCREATED = get_ipif_hub_repo_AUTOCREATED_instance()

    ingest_person_or_source(Person, person1_data, repo)
    ingest_person_or_source(Source, source1_data, repo)
    ingest_statement(statement1_data, repo)

    ingest_factoid(factoid1_data, repo)

    ingest_statement(statement2_data, repo)

    ingest_factoid(factoid1_data_update, repo)

    f: Factoid = Factoid.objects.get(identifier="http://test.com/factoids/Factoid1")
    assert f.local_id == "Factoid1"
    assert f.createdBy == "Researcher1"
    assert f.createdWhen == datetime.date(2012, 4, 23)
    assert f.modifiedBy == "Researcher2"
    assert f.modifiedWhen == datetime.date(2012, 4, 24)

    assert f.person == Person.objects.get(identifier="http://test.com/persons/Person1")
    assert f.source == Source.objects.get(identifier="http://test.com/sources/Source1")
    assert (
        Statement.objects.get(
            identifier="http://test.com/statements/St1-John-Smith-Name"
        )
        in f.statements.all()
    )
    assert (
        Statement.objects.get(
            identifier="http://test.com/statements/St2-jsmith-teacher"
        )
        in f.statements.all()
    )

    p: Person = Person.objects.get(identifier="http://persons.com/mrsSpenceley")
    assert p.ipif_repo == AUTOCREATED


@pytest.mark.django_db
def test_data_ingestion_function(
    factoid1_data: dict,
    person1_data: dict,
    source1_data: dict,
    statement1_data: dict,
    repo,
):
    data = {
        "factoids": [factoid1_data],
        "persons": [person1_data],
        "sources": [source1_data],
        "statements": [statement1_data],
    }
    ingest_data("testrepo", data)
