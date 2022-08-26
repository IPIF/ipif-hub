import pytest

from ipif_hub.models import URI, MergePerson, Person
from ipif_hub.signals.handlers import handle_merge_person_from_person_update
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
def test_handle_merge_person_from_person_update_initial(person):
    handle_merge_person_from_person_update(person)
    merge_person = MergePerson.objects.filter(persons__uris__in=person.uris.all())
    assert merge_person.first()
    assert len(MergePerson.objects.all()) == 1
    assert merge_person.first().persons.first() == person


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
