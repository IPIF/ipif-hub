import pytest
from django.test import override_settings
from django.core.management import call_command

from ipif_hub.models import IpifRepo, Person, Source, Statement, Factoid, Place
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
        call_command("clear_index", interactive=False, verbosity=0)


test_repo_no_slug = {
    "endpoint_name": "TestRepo",
    "endpoint_uri": "http://test.com/",
    "refresh_frequency": "daily",
    "refresh_time": datetime.time(0, 0, 0),
    "endpoint_is_ipif": False,
    "description": "A test repo",
    "provider": "University of Test",
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
def person(repo):
    p = Person(
        local_id="person1", label="Person One", ipif_repo=repo, **created_modified
    )
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
        local_id="related_person",
        label="Related Person",
        ipif_repo=repo,
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
@pytest.mark.django_db(transaction=True)
def factoid(repo, person, source, statement):
    f = Factoid(
        local_id="factoid1", label="Factoid One", ipif_repo=repo, **created_modified
    )
    f.person = person
    f.source = source
    f.save()
    f.statement.add(statement)
    f.save()
    yield f
