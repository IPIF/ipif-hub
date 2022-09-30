import pytest
from django.db import IntegrityError

from ipif_hub.models import IpifRepo, MergePerson, MergeSource, Person, Source
from ipif_hub.signals.handler_utils import build_extra_uris
from ipif_hub.tests.conftest import created_modified, test_repo_no_slug

# from ipif_hub.search_indexes import PersonIndex


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


@pytest.mark.django_db(transaction=True)
def test_create_merge_person_and_connect_two_persons(
    mute_signals, repo, repo2, person, person_sameAs
):
    mp = MergePerson(**created_modified)
    mp.save()
    mp.persons.add(person, person_sameAs)

    # assert mp.uris.first().uri == "http://alternative.com/person1"

    # assert mp.uri_set == {"http://alternative.com/person1"}

    assert person in mp.persons.all()

    assert MergePerson.objects.filter(persons__uris=mp.uris.first()).first() == mp


@pytest.mark.django_db(transaction=True)
def test_merge_person_created_by_person_created(repo, personNotSameAs, factoid):
    assert personNotSameAs in Person.objects.all()

    assert MergePerson.objects.all()


@pytest.mark.django_db(transaction=True)
def test_merge_source_created_by_source_created(repo, sourceNotSameAs, factoid):
    assert sourceNotSameAs in Source.objects.all()

    assert MergeSource.objects.all()


@pytest.mark.django_db(transaction=True)
def test_source_has_additional_uris_on_save(repo, source, factoid):
    assert source in Source.objects.all()

    uris = {uri.uri for uri in source.uris.all()}
    assert uris == {
        "http://sources.com/source1",
        "http://sources.com/sourceSameAs",
        "http://test.com/sources/source1",
        *build_extra_uris(source),
    }


@pytest.mark.django_db(transaction=True)
def test_person_has_additional_uris_on_save(repo, person, factoid):
    assert person in Person.objects.all()

    uris = {uri.uri for uri in person.uris.all()}
    assert uris == {
        "http://alternative.com/person1",
        *build_extra_uris(person),
    }


"""
OK:

when we save a person —- always add URLs first

check all of those persons URIs -- get all the MergePersons with those URIs

- if NONE: create a new MergePerson, adding person
- if ONE: ... nothing: it's already there: add person
- if N: --- take first, add persons from the other ones, delete the others

-- on delete persons... 
    use that algorithm...



"""
