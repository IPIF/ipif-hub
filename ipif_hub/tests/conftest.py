import datetime

import pytest
from django.core.management import call_command
from django.db.models.signals import (
    m2m_changed,
    post_delete,
    post_save,
    pre_delete,
    pre_save,
)
from django.test import override_settings

from ipif_hub.models import (
    URI,
    Factoid,
    IpifRepo,
    Person,
    Place,
    Source,
    Statement,
    get_ipif_hub_repo_AUTOCREATED_instance,
)


@pytest.fixture(autouse=True)
@pytest.mark.django_db()
def _setup():
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


# tests/intergration_tests/conftest.py


@pytest.fixture  # Automatically use in tests.
def mute_signals():
    # Skip applying, if marked with `enabled_signals`

    signals = [pre_save, post_save, pre_delete, post_delete, m2m_changed]
    restore = {}
    for signal in signals:
        # Temporally remove the signal's receivers (a.k.a attached functions)
        restore[signal] = signal.receivers
        signal.receivers = []

    yield

    # When the test tears down, restore the signals.
    for signal, receivers in restore.items():
        signal.receivers = receivers


@pytest.fixture()
@pytest.mark.django_db(transaction=True)
def repo():
    # Create a repo
    repo = IpifRepo(endpoint_slug="testrepo", **test_repo_no_slug)
    repo.save()
    return repo


@pytest.fixture()
@pytest.mark.django_db(transaction=True)
def repo2():
    repo = IpifRepo(endpoint_slug="testrepo2", **test_repo_no_slug2)
    repo.save()
    return repo


@pytest.fixture()
@pytest.mark.django_db(transaction=True)
def uri():
    uri = URI(uri="http://person_uri.com/person1")
    uri.save()
    return uri


@pytest.fixture()
@pytest.mark.django_db(transaction=True)
def place():
    place = Place(uri="http://places.com/place1", label="place1")
    place.save()
    return place


@pytest.fixture()
@pytest.mark.django_db(transaction=True)
def alt_uri():
    uri = URI(uri="http://alternative.com/person1")
    uri.save()
    return uri


@pytest.fixture()
@pytest.mark.django_db(transaction=True)
def uriNotSameAs():
    uri = URI(uri="http://notSameAs.com/person2")
    uri.save()
    return uri


@pytest.fixture()
@pytest.mark.django_db(transaction=True)
def person(repo, alt_uri) -> Person:
    p = Person(
        local_id="person1", label="Person One", ipif_repo=repo, **created_modified
    )
    p.save()

    p.uris.add(alt_uri)
    p.save()
    return p


@pytest.fixture()
@pytest.mark.django_db(transaction=True)
def person_sameAs(repo2, alt_uri):
    p = Person(
        local_id="person_sameAs",
        label="Person SameAs",
        ipif_repo=repo2,
        **created_modified,
    )
    p.save()
    p.uris.add(alt_uri)
    p.save()
    return p


@pytest.fixture()
@pytest.mark.django_db(transaction=True)
def person2(repo, alt_uri):
    p = Person(
        local_id="person2", label="Person Two", ipif_repo=repo, **created_modified
    )
    p.save()
    p.uris.add(alt_uri)
    p.save()
    return p


@pytest.fixture()
@pytest.mark.django_db(transaction=True)
def personNotSameAs(repo, uriNotSameAs):
    p = Person(
        local_id="personNotSameAs",
        label="Person NotSameAs",
        ipif_repo=repo,
        **created_modified,
    )
    p.save()
    p.uris.add(uriNotSameAs)
    return p


@pytest.fixture()
@pytest.mark.django_db(transaction=True)
def sourceSameAsURI():
    uri = URI(uri="http://sources.com/sourceSameAs")
    uri.save()
    return uri


@pytest.fixture()
@pytest.mark.django_db(transaction=True)
def source(repo, sourceSameAsURI):
    s: Source = Source(
        local_id="source1", label="Source One", ipif_repo=repo, **created_modified
    )
    s.save()

    uri = URI(uri="http://sources.com/source1")
    uri.save()
    s.uris.add(uri)

    s.uris.add(sourceSameAsURI)
    return s


@pytest.fixture()
@pytest.mark.django_db(transaction=True)
def sourceSameAs(repo, sourceSameAsURI):
    s = Source(
        local_id="sourceSameAs",
        label="Source SameAs",
        ipif_repo=repo,
        **created_modified,
    )
    s.save()

    s.uris.add(sourceSameAsURI)

    return s


@pytest.fixture()
@pytest.mark.django_db(transaction=True)
def sourceNotSameAs(repo):
    s = Source(
        local_id="sourceNotSameAs",
        label="Source NotSameAs",
        ipif_repo=repo,
        **created_modified,
    )
    s.save()
    uri = URI(uri="http://notsamesource.com/")
    uri.save()
    s.uris.add(uri)
    return s


@pytest.fixture()
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
    return st


@pytest.fixture()
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
    return st


@pytest.fixture()
@pytest.mark.django_db(transaction=True)
def factoid(repo, person, source, statement):
    f = Factoid(
        local_id="factoid1",
        label="Factoid One",
        ipif_repo=repo,
        **created_modified,
    )
    f.person = person
    f.source = source
    f.save()
    f.statements.add(statement)
    f.save()
    return f


@pytest.fixture()
@pytest.mark.django_db(transaction=True)
def factoid2(repo, person, source, statement2):
    f = Factoid(
        local_id="factoid2",
        label="Factoid Two",
        ipif_repo=repo,
        **created_modified,
    )
    f.person = person
    f.source = source
    f.save()
    f.statements.add(statement2)
    f.save()
    return f


@pytest.fixture()
@pytest.mark.django_db(transaction=True)
def factoid3(repo, person_sameAs, source, statement2):
    f = Factoid(
        local_id="factoid3",
        label="Factoid Three",
        ipif_repo=repo,
        **created_modified,
    )
    f.person = person_sameAs
    f.source = source
    f.save()
    f.statements.add(statement2)
    f.save()
    return f


@pytest.fixture()
@pytest.mark.django_db(transaction=True)
def factoid4(repo, personNotSameAs, source, statement2):
    f = Factoid(
        local_id="factoid4",
        label="Factoid Four",
        ipif_repo=repo,
        **created_modified,
    )
    f.person = personNotSameAs
    f.source = source
    f.save()
    f.statements.add(statement2)
    f.save()
    return f
