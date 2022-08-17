import datetime
import json

from django.db import IntegrityError

from ipif_hub.models import Factoid, Person, IpifRepo, Source, Statement

# from ipif_hub.search_indexes import PersonIndex

import pytest
from ipif_hub.tests.conftest import (
    repo,
    test_repo_no_slug,
    created_modified,
    person_sameAs,
    repo2,
)


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

    looked_up_p = Person.objects.get(identifier="http://test.com/persons/person1")
    assert looked_up_p.identifier == p.identifier


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
