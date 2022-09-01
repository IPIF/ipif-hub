import pytest

from ipif_hub.models import URI, MergePerson, MergeSource, Person, Source
from ipif_hub.signals.handlers import (
    handle_merge_person_from_person_update,
    handle_merge_source_from_source_update,
)
from ipif_hub.tests.conftest import created_modified


@pytest.mark.django_db(transaction=True)
def test_handle_merge_person_called_by_m2m_changed(repo):
    uri1 = URI(uri="http://one.com")
    uri1.save()

    p1 = Person(
        local_id="person1",
        label="person1",
        ipif_repo=repo,
        **created_modified,
    )
    p1.save()
    p1.uris.add(uri1)

    merge_persons = MergePerson.objects.all()
    assert len(merge_persons) == 1


@pytest.mark.django_db(transaction=True)
def test_handle_merge_person_called_by_save(repo):

    p1 = Person(
        local_id="person1",
        label="person1",
        ipif_repo=repo,
        **created_modified,
    )
    p1.save()

    merge_persons = MergePerson.objects.all()
    assert len(merge_persons) == 1


@pytest.mark.django_db(transaction=True)
def test_handle_merge_source_called_by_m2m_changed(repo):
    uri1 = URI(uri="http://one.com")
    uri1.save()

    s1 = Source(
        local_id="source1",
        label="source1",
        ipif_repo=repo,
        **created_modified,
    )
    s1.save()
    s1.uris.add(uri1)

    merge_sources = MergeSource.objects.all()
    assert len(merge_sources) == 1
    ms: MergeSource = merge_sources.first()
    assert uri1 in ms.uris


@pytest.mark.django_db(transaction=True)
def test_handle_merge_source_called_by_save(repo):

    s1 = Source(
        local_id="source1",
        label="source1",
        ipif_repo=repo,
        **created_modified,
    )
    s1.save()

    merge_sources = MergeSource.objects.all()
    assert len(merge_sources) == 1


@pytest.mark.django_db(transaction=True)
def test_handle_merge_person_from_person_update_initial(person):
    handle_merge_person_from_person_update(person)
    merge_person = MergePerson.objects.filter(persons__uris__in=person.uris.all())
    assert merge_person.first()
    assert len(MergePerson.objects.all()) == 1
    assert merge_person.first().persons.first() == person


@pytest.mark.django_db(transaction=True)
def test_handle_merge_source_from_source_update_initial(source):
    handle_merge_source_from_source_update(source)
    merge_source = MergeSource.objects.filter(sources__uris__in=source.uris.all())
    assert merge_source.first()
    assert len(MergeSource.objects.all()) == 1
    assert merge_source.first().sources.first() == source


@pytest.mark.django_db
def test_handle_merge_person_from_person_update_add_second_person(
    person, person_sameAs
):
    handle_merge_person_from_person_update(person)

    assert len(MergePerson.objects.all()) == 1

    handle_merge_person_from_person_update(person_sameAs)

    assert len(MergePerson.objects.all()) == 1

    merge_person = MergePerson.objects.first()
    assert person in merge_person.persons.all()
    assert person_sameAs in merge_person.persons.all()


@pytest.mark.django_db
def test_handle_merge_source_from_source_update_add_second_source(source, sourceSameAs):
    handle_merge_source_from_source_update(source)

    assert len(MergeSource.objects.all()) == 1

    handle_merge_source_from_source_update(sourceSameAs)

    assert len(MergeSource.objects.all()) == 1

    merge_source = MergeSource.objects.first()
    assert source in merge_source.sources.all()
    assert sourceSameAs in merge_source.sources.all()


@pytest.mark.django_db
def test_handle_merge_person_from_person_update_add_join(mute_signals, repo):
    uri1 = URI(uri="http://one.com")
    uri1.save()

    uri2 = URI(uri="http://two.com")
    uri2.save()

    p1 = Person(
        local_id="person1",
        label="person1",
        ipif_repo=repo,
        **created_modified,
    )
    p1.save()
    p1.uris.add(uri1)

    p2 = Person(
        local_id="person2",
        label="person2",
        ipif_repo=repo,
        **created_modified,
    )
    p2.save()
    p2.uris.add(uri2)

    p3 = Person(
        local_id="person3",
        label="person3",
        ipif_repo=repo,
        **created_modified,
    )
    p3.save()
    p3.uris.add(uri1, uri2)

    handle_merge_person_from_person_update(p1)

    assert len(MergePerson.objects.all()) == 1

    handle_merge_person_from_person_update(p2)

    assert len(MergePerson.objects.all()) == 2

    handle_merge_person_from_person_update(p3)

    merge_persons = MergePerson.objects.all()
    assert len(merge_persons) == 1

    merge_person = merge_persons.first()

    assert p1 in merge_person.persons.all()
    assert p2 in merge_person.persons.all()
    assert p3 in merge_person.persons.all()

    assert uri1 in merge_person.uris
    assert uri2 in merge_person.uris


@pytest.mark.django_db
def test_handle_merge_source_from_source_update_add_join(mute_signals, repo):
    uri1 = URI(uri="http://one.com")
    uri1.save()

    uri2 = URI(uri="http://two.com")
    uri2.save()

    s1 = Source(
        local_id="source1",
        label="source1",
        ipif_repo=repo,
        **created_modified,
    )
    s1.save()
    s1.uris.add(uri1)

    s2 = Source(
        local_id="source2",
        label="source2",
        ipif_repo=repo,
        **created_modified,
    )
    s2.save()
    s2.uris.add(uri2)

    s3 = Source(
        local_id="source3",
        label="source3",
        ipif_repo=repo,
        **created_modified,
    )
    s3.save()
    s3.uris.add(uri1, uri2)

    handle_merge_source_from_source_update(s1)

    assert len(MergeSource.objects.all()) == 1

    handle_merge_source_from_source_update(s2)

    assert len(MergeSource.objects.all()) == 2

    handle_merge_source_from_source_update(s3)

    merge_sources = MergeSource.objects.all()
    assert len(merge_sources) == 1

    merge_source = merge_sources.first()

    assert s1 in merge_source.sources.all()
    assert s2 in merge_source.sources.all()
    assert s3 in merge_source.sources.all()

    assert uri1 in merge_source.uris
    assert uri2 in merge_source.uris


@pytest.mark.django_db(transaction=True)
def test_handle_delete_person_updates_merge_persons(repo):

    # Set up — create three persons with a joining URI
    uri1 = URI(uri="http://one.com")
    uri1.save()

    uri2 = URI(uri="http://two.com")
    uri2.save()

    p1 = Person(
        local_id="person1",
        label="person1",
        ipif_repo=repo,
        **created_modified,
    )
    p1.save()
    p1.uris.add(uri1)

    p4 = Person(
        local_id="person4",
        label="person4",
        ipif_repo=repo,
        **created_modified,
    )
    p4.save()
    p4.uris.add(uri1)

    p2 = Person(
        local_id="person2",
        label="person2",
        ipif_repo=repo,
        **created_modified,
    )
    p2.save()
    p2.uris.add(uri2)

    p3 = Person(
        local_id="person3",
        label="person3",
        ipif_repo=repo,
        **created_modified,
    )
    p3.save()
    p3.uris.add(uri1, uri2)

    merge_persons = MergePerson.objects.all()
    assert len(merge_persons) == 1

    # Now test
    p3.delete()

    merge_persons = MergePerson.objects.all()
    assert len(merge_persons) == 2

    # Check that all the persons are attached to a MergePerson object
    persons_to_account_for = [p1, p2, p4]

    for mp in merge_persons:
        for person in mp.persons.all():
            persons_to_account_for.remove(person)

    assert persons_to_account_for == []


@pytest.mark.django_db(transaction=True)
def test_handle_delete_source_updates_merge_sources(repo):

    # Set up — create three persons with a joining URI
    uri1 = URI(uri="http://one.com")
    uri1.save()

    uri2 = URI(uri="http://two.com")
    uri2.save()

    s1 = Source(
        local_id="source1",
        label="source1",
        ipif_repo=repo,
        **created_modified,
    )
    s1.save()
    s1.uris.add(uri1)

    s4 = Source(
        local_id="source4",
        label="source4",
        ipif_repo=repo,
        **created_modified,
    )
    s4.save()
    s4.uris.add(uri1)

    s2 = Source(
        local_id="source2",
        label="source2",
        ipif_repo=repo,
        **created_modified,
    )
    s2.save()
    s2.uris.add(uri2)

    s3 = Source(
        local_id="source3",
        label="source3",
        ipif_repo=repo,
        **created_modified,
    )
    s3.save()
    s3.uris.add(uri1, uri2)

    merge_sources = MergeSource.objects.all()
    assert len(merge_sources) == 1

    # Now test
    s3.delete()

    merge_sources = MergeSource.objects.all()
    assert len(merge_sources) == 2

    # Check that all the persons are attached to a MergePerson object
    sources_to_account_for = [s1, s2, s4]

    for ms in merge_sources:
        for source in ms.sources.all():
            sources_to_account_for.remove(source)

    assert sources_to_account_for == []
