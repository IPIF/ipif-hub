import json

import pytest
from django.db import transaction

from ipif_hub.models import Factoid, MergePerson, MergeSource, Person, Source, Statement
from ipif_hub.search_indexes import MergePersonIndex, MergeSourceIndex, PersonIndex
from ipif_hub.tests.conftest import created_modified


@pytest.mark.django_db(transaction=True)
def test_entity_is_in_haystack(repo):
    """Test created person is pushed to Haystack on save"""
    with transaction.atomic():
        p = Person(local_id="person1", ipif_repo=repo, **created_modified)
        p.save()
    import time

    time.sleep(5)
    pi = PersonIndex.objects.filter(identifier="http://test.com/persons/person1")[0]
    assert pi.identifier == p.identifier


@pytest.mark.django_db(transaction=True)
def test_adding_factoid_triggers_update_of_person_index(repo):
    """Test adding a factoid related to Person causes index to refresh"""

    # Create Person
    p = Person(local_id="person1", ipif_repo=repo, **created_modified)
    p.save()

    # Confirm factoid-refs in index is empty
    pi = PersonIndex.objects.filter(identifier="http://test.com/persons/person1")[0]

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
    f.statements.add(st)
    f.save()

    # Check everything that should be in the index is
    pi = PersonIndex.objects.filter(identifier="http://test.com/persons/person1")[0]
    pi_json = json.loads(pi.pre_serialized)
    print(pi_json)
    assert len(pi_json["factoid-refs"]) == 1
    assert (
        pi_json["factoid-refs"][0]["source-ref"]["@id"]
        == "http://test.com/sources/source1"
    )

    assert (
        pi_json["factoid-refs"][0]["statement-refs"][0]["@id"]
        == "http://test.com/statements/statement1"
    )


@pytest.mark.django_db(transaction=True)
def test_merge_person_created(
    person,
    statement2,
    source,
    factoid2,
    person_sameAs,
):
    merge_persons = MergePersonIndex.objects.filter(ipif_type="mergeperson")
    assert len(merge_persons) == 1

    merge_person = merge_persons[0]

    data = json.loads(merge_person.pre_serialized)

    assert data
    assert data["factoid-refs"]
    print(data["factoid-refs"])
    assert data["factoid-refs"][0]["@id"] == "http://test.com/factoids/factoid2"


@pytest.mark.django_db(transaction=True)
def test_merge_person_create_with_no_uri(
    factoid_person_no_uri,
    person_no_uri,
):
    assert len(MergePerson.objects.all()) == 1

    merge_persons = MergePersonIndex.objects.filter(ipif_type="mergeperson")
    assert len(merge_persons) == 1

    merge_person = merge_persons[0]

    data = json.loads(merge_person.pre_serialized)

    assert data
    assert data["factoid-refs"]
    print(data["factoid-refs"])
    assert (
        data["factoid-refs"][0]["@id"]
        == "http://test.com/factoids/factoid_person_no_uri"
    )


@pytest.mark.django_db(transaction=True)
def test_merge_source_created(
    person,
    statement,
    source,
    sourceSameAs,
    factoid,
):
    merge_sources = MergeSourceIndex.objects.filter(ipif_type="mergesource")
    print(merge_sources)
    assert len(merge_sources) == 1

    merge_source = merge_sources[0]

    data = json.loads(merge_source.pre_serialized)
    assert data
    assert data["factoid-refs"]
    assert data["factoid-refs"][0]["@id"] == "http://test.com/factoids/factoid1"


@pytest.mark.django_db(transaction=True)
def test_merge_person_deleted_from_index(
    person,
    statement2,
    source,
    factoid2,
    person_sameAs,
):
    merge_persons = MergePersonIndex.objects.filter(ipif_type="mergeperson")
    assert len(merge_persons) == 1

    MergePerson.objects.first().delete()

    merge_persons = MergePersonIndex.objects.filter(ipif_type="mergeperson")
    assert len(merge_persons) == 0


@pytest.mark.django_db(transaction=True)
def test_merge_source_deleted_from_index(
    person,
    statement,
    source,
    sourceSameAs,
    factoid,
):
    merge_sources = MergeSourceIndex.objects.filter(ipif_type="mergesource")
    assert len(merge_sources) == 1

    MergeSource.objects.first().delete()

    merge_sources = MergeSourceIndex.objects.filter(ipif_type="mergesource")
    assert len(merge_sources) == 0
