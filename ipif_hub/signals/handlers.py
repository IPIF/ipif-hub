import datetime
import itertools
from typing import List, Any

import numpy as np

from django.db.models.signals import post_save, m2m_changed, pre_delete
from django.dispatch import receiver
from django.db import transaction
from ipif_hub.models import Person, Source, Statement, Factoid, MergePerson, MergeSource


from ipif_hub.tasks import (
    update_factoid_index,
    update_person_index,
    update_source_index,
    update_statement_index,
)


def handle_merge_person_from_person_update(new_person):
    """Receives a Person object"""

    matching_merge_persons = MergePerson.objects.filter(
        persons__uris__in=new_person.uris.all()
    )
    if not matching_merge_persons:
        # Create new
        merge_person = MergePerson(
            createdBy="ipif-hub",
            createdWhen=datetime.date.today(),
            modifiedBy="ipif-hub",
            modifiedWhen=datetime.date.today(),
        )
        merge_person.save()
        merge_person.persons.add(new_person)

    elif len(matching_merge_persons) == 1:
        merge_person = matching_merge_persons.first()
        merge_person.persons.add(new_person)

    elif len(matching_merge_persons) > 1:
        all_persons = []
        for merge_person in matching_merge_persons:
            all_persons = [*all_persons, *merge_person.persons.all()]
            merge_person.delete()
        new_merged_person = MergePerson(
            createdBy="ipif-hub",
            createdWhen=datetime.date.today(),
            modifiedBy="ipif-hub",
            modifiedWhen=datetime.date.today(),
        )
        new_merged_person.save()
        new_merged_person.persons.add(*all_persons, new_person)


def merge(persons: list, results=None) -> Any:
    """This code suggested by Philipp Petersen
    (https://ufind.univie.ac.at/de/person.html?id=109645)


    It works, which is cool. It also uses Numpy, which is unnecessary.

    """

    all_values = list(set(itertools.chain(*persons)))

    persons_copy = persons.copy()

    for k in range(len(all_values)):

        mergers = np.zeros(len(persons_copy))

        for p in range(len(persons_copy)):
            if all_values[k] in persons_copy[p]:
                mergers[p] = 1

        if np.sum(mergers) > 1:

            merge_these_please = np.where(mergers == 1)[0]
            ready_to_merge = [persons_copy[i] for i in merge_these_please]
            merged_stuff = np.unique(np.concatenate(ready_to_merge))

            sorted_ = np.sort(merge_these_please)  # probably not necessary

            for q in sorted_[::-1]:
                persons_copy.pop(q)
            persons_copy.append(list(merged_stuff))
    return persons_copy


def handle_delete_person_updating_merge_persons(person_to_delete: Person) -> None:
    """On pre-delete of a person, remove the person's MergePerson
    (delete it later). Find all remaining persons attached to that
    MergePerson, and regroup them by common URIs. Then create
    a new MergePerson for each group, attaching relevant persons.
    """
    old_merge_person = MergePerson.objects.get(persons=person_to_delete)
    remaining_persons = old_merge_person.persons.exclude(pk=person_to_delete.pk)
    uris_to_group = [
        [uri.uri for uri in person.uris.all()] for person in remaining_persons
    ]
    print(uris_to_group)
    merged_uri_groups: List[list] = merge(uris_to_group)

    for uri_group in merged_uri_groups:
        persons = (
            Person.objects.filter(uris__uri__in=uri_group)
            .exclude(pk=person_to_delete.pk)
            .distinct()
        )
        new_merged_person = MergePerson(
            createdBy="ipif-hub",
            createdWhen=datetime.date.today(),
            modifiedBy="ipif-hub",
            modifiedWhen=datetime.date.today(),
        )
        new_merged_person.save()
        new_merged_person.persons.add(*persons)
    old_merge_person.delete()


@receiver(m2m_changed, sender=MergePerson.persons.through)
def merge_person_m2m_changed(sender, instance, **kwargs):
    # TODO: TRIGGER INDEXING OF MergePerson
    pass


# Off the top of my head, it should not be necessary to index
# the MergePerson after just a save; the actual change will always
# be on changing the m2m of person
@receiver(post_save, sender=MergePerson)
def index(sender, instance, **kwargs):
    pass


@receiver(m2m_changed, sender=MergeSource.sources.through)
def merge_source_m2m_changed(sender, instance, **kwargs):
    # print("MP_m2mchanged SOURCE CALLED")
    pass


@receiver(post_save, sender=Factoid)
def factoid_post_save(sender, instance, **kwargs):
    transaction.on_commit(lambda: update_factoid_index.delay(instance.pk))


@receiver(post_save, sender=Person)
def person_post_save(sender, instance, **kwargs):

    transaction.on_commit(lambda: update_person_index.delay(instance.pk))


@receiver(m2m_changed, sender=Person.uris.through)
def person_m2m_changed(sender, instance, **kwargs):

    handle_merge_person_from_person_update(instance)


@receiver(pre_delete, sender=Person)
def person_pre_delete(sender, instance, **kwargs):
    print(instance)
    handle_delete_person_updating_merge_persons(instance)


@receiver(post_save, sender=Source)
def source_post_save(sender, instance, **kwargs):
    transaction.on_commit(lambda: update_source_index.delay(instance.pk))


@receiver(post_save, sender=Statement)
def statement_post_save(sender, instance, **kwargs):
    transaction.on_commit(lambda: update_statement_index.delay(instance.pk))
