import datetime
import json

from django.db import IntegrityError

from ipif_hub.models import Factoid, Person, IpifRepo, Source, Statement
from ipif_hub.search_indexes import PersonIndex

import pytest
from ipif_hub.tests.conftest import repo, test_repo_no_slug, created_modified


@pytest.mark.django_db
def test_create_ipif_repo_without_endpoint_slug_raises_exception():
    repo = IpifRepo(**test_repo_no_slug)
    with pytest.raises(IntegrityError):
        repo.save()


@pytest.mark.django_db
def test_create_repo_succeeds_with_endpoint_slug():
    repo = IpifRepo(endpoint_slug="testrepo", **test_repo_no_slug)
    repo.save()


@pytest.mark.django_db
def test_get_repo(repo):
    assert repo.pk == IpifRepo.objects.first().pk


@pytest.mark.django_db
def test_create_person_and_correct_id(repo):
    p = Person(local_id="person1", ipif_repo=repo, **created_modified)
    p.save()

    # Test the qualified uri works
    uri_id = p.build_uri_id_from_slug("person1")
    assert uri_id == "http://test.com/persons/person1"


@pytest.mark.django_db
def test_created_person_in_db(repo):
    p = Person(local_id="person1", ipif_repo=repo, **created_modified)
    p.save()

    looked_up_p = Person.objects.get(pk="http://test.com/persons/person1")
    assert looked_up_p.pk == p.pk


@pytest.mark.django_db
def test_create_person_and_correct_id_when_id_is_uri(repo):
    # If the id is already a URL, we can use that instead
    p = Person(
        local_id="http://test.com/persons/person1", ipif_repo=repo, **created_modified
    )
    p.save()

    # Test the qualified uri works
    uri_id = p.build_uri_id_from_slug("http://test.com/persons/person1")
    assert uri_id == "http://test.com/persons/person1"


@pytest.mark.django_db
def test_entity_is_in_haystack(repo):
    """Test created person is pushed to Haystack on save"""
    p = Person(local_id="person1", ipif_repo=repo, **created_modified)
    p.save()

    pi = PersonIndex.objects.filter(
        id="ipif_hub.person.http://test.com/persons/person1"
    )[0]
    assert pi.pk == p.pk


@pytest.mark.django_db(transaction=True)
def test_adding_factoid_triggers_update_of_person_index(repo):
    """Test adding a factoid related to Person causes index to refresh"""

    # Create Person
    p = Person(local_id="person1", ipif_repo=repo, **created_modified)
    p.save()

    # Confirm factoid-refs in index is empty
    pi = PersonIndex.objects.filter(
        id="ipif_hub.person.http://test.com/persons/person1"
    )[0]

    pi_json = json.loads(pi.pre_serialized)
    assert len(pi_json["factoid-refs"]) == 0

    # Create Source and Statement
    s = Source(local_id="source1", ipif_repo=repo, **created_modified)
    s.save()
    st = Statement(
        local_id="statement1", ipif_repo=repo, **created_modified, name="John Smith"
    )
    st.save()

    # Create Factoid
    f = Factoid(local_id="factoid1", ipif_repo=repo, **created_modified)
    f.person = p
    f.source = s
    f.save()
    f.statement.add(st)
    f.save()

    # Check everything that should be in the index is
    pi = PersonIndex.objects.filter(
        id="ipif_hub.person.http://test.com/persons/person1"
    )[0]
    pi_json = json.loads(pi.pre_serialized)

    assert len(pi_json["factoid-refs"]) == 1
    assert (
        pi_json["factoid-refs"][0]["source-ref"]["@id"]
        == "http://test.com/sources/source1"
    )

    assert (
        pi_json["factoid-refs"][0]["statement-refs"][0]["@id"]
        == "http://test.com/statements/statement1"
    )
