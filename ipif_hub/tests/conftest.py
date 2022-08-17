import pytest
from django.test import override_settings
from django.core.management import call_command

from ipif_hub.models import (
    IpifRepo,
    Person,
    Source,
    Statement,
    Factoid,
    Place,
    URI,
    get_ipif_hub_repo_AUTOCREATED_instance,
)
import datetime


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
        # call_command("clear_index", interactive=False, verbosity=0)


test_repo_no_slug = {
    "endpoint_name": "TestRepo",
    "endpoint_uri": "http://test.com/",
    "refresh_frequency": "daily",
    "refresh_time": datetime.time(0, 0, 0),
    "endpoint_is_ipif": False,
    "description": "A test repo",
    "provider": "University of Test",
}

test_repo_no_slug2 = {
    "endpoint_name": "TestRepo2",
    "endpoint_uri": "http://test2.com/",
    "refresh_frequency": "daily",
    "refresh_time": datetime.time(0, 0, 0),
    "endpoint_is_ipif": False,
    "description": "A test repo2",
    "provider": "University of Test2",
}

created_modified = {
    "createdWhen": datetime.date(2022, 3, 1),
    "createdBy": "researcher1",
    "modifiedWhen": datetime.date(2022, 4, 1),
    "modifiedBy": "researcher2",
}


@pytest.fixture
@pytest.mark.django_db(transaction=True)
def repo():
    # Create a repo
    repo = IpifRepo(endpoint_slug="testrepo", **test_repo_no_slug)
    repo.save()
    yield repo


@pytest.fixture
@pytest.mark.django_db(transaction=True)
def repo2():
    repo = IpifRepo(endpoint_slug="testrepo2", **test_repo_no_slug2)
    repo.save()
    yield repo


@pytest.fixture
@pytest.mark.django_db(transaction=True)
def uri():
    uri = URI(uri="http://person_uri.com/person1")
    uri.save()
    return uri


@pytest.fixture
@pytest.mark.django_db(transaction=True)
def place():
    place = Place(uri="http://places.com/place1", label="place1")
    place.save()
    return place


@pytest.fixture
@pytest.mark.django_db(transaction=True)
def person(repo):
    p = Person(
        local_id="person1", label="Person One", ipif_repo=repo, **created_modified
    )
    p.save()
    uri = URI(uri="http://alternative.com/person1")
    uri.save()
    p.uris.add(uri)
    p.save()
    yield p


@pytest.fixture
@pytest.mark.django_db(transaction=True)
def person_sameAs(repo2):
    p = Person(
        local_id="person_sameAs",
        label="Person SameAs",
        ipif_repo=repo2,
        **created_modified,
    )
    p.save()
    uri = URI(uri="http://alternative.com/person1")
    uri.save()
    p.uris.add(uri)
    p.save()
    yield p


@pytest.fixture
@pytest.mark.django_db(transaction=True)
def person2(repo):
    p = Person(
        local_id="person2", label="Person Two", ipif_repo=repo, **created_modified
    )
    p.save()
    uri = URI(uri="http://alternative.com/person2")
    uri.save()
    p.uris.add(uri)
    p.save()
    yield p


@pytest.fixture
@pytest.mark.django_db(transaction=True)
def source(repo):
    s = Source(
        local_id="source1", label="Source One", ipif_repo=repo, **created_modified
    )
    s.save()
    yield s


@pytest.fixture
@pytest.mark.django_db(transaction=True)
def statement(repo):
    related_person = Person(
        local_id="http://related.com/person1",
        label="Related Person",
        ipif_repo=get_ipif_hub_repo_AUTOCREATED_instance(),
        **created_modified,
    )
    related_person.save()

    place = Place(label="Nowhere", uri="http://places.com/nowhere")
    place.save()

    st = Statement(
        local_id="statement1",
        label="Statement One",
        ipif_repo=repo,
        **created_modified,
        statementType_uri="http://all_purpose_statement.com",
        statementType_label="All Purpose Statement",
        name="John Smith",
        role_uri="http://role.com/unemployed",
        role_label="unemployed",
        date_sortdate=datetime.date(1900, 1, 1),
        date_label="1 Jan 1900",
        memberOf_uri="http://orgs.com/madeup",
        memberOf_label="Made Up Organisation",
        statementText="John Smith is a Member of Madeup",
    )
    st.save()
    st.relatesToPerson.add(related_person)
    st.places.add(place)
    st.save()
    yield st


@pytest.fixture
@pytest.mark.django_db
def statement2(repo):
    st = Statement(
        local_id="statement2",
        label="Statement Two",
        ipif_repo=repo,
        **created_modified,
        statementType_uri="http://namingStatement",
        statementType_label="naming",
        name="Johannes Schmitt",
    )

    st.save()
    yield st


@pytest.fixture
@pytest.mark.django_db(transaction=True)
def factoid(repo, person, source, statement):
    f = Factoid(
        local_id="factoid1", label="Factoid One", ipif_repo=repo, **created_modified
    )
    f.person = person
    f.source = source
    f.save()
    f.statements.add(statement)
    f.save()
    yield f


@pytest.fixture
@pytest.mark.django_db(transaction=True)
def factoid2(repo, person, source, statement2):
    f = Factoid(
        local_id="factoid2", label="Factoid Two", ipif_repo=repo, **created_modified
    )
    f.person = person
    f.source = source
    f.save()
    f.statements.add(statement2)
    f.save()
    yield f
