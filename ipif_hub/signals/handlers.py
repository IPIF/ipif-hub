import datetime
import itertools
from typing import Any, List, Union

import numpy as np
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch import receiver

from ipif_hub.models import (
    URI,
    Factoid,
    MergePerson,
    MergeSource,
    Person,
    Source,
    Statement,
    get_ipif_hub_repo_AUTOCREATED_instance,
)
from ipif_hub.tasks import (
    update_factoid_index,
    update_merge_person_index,
    update_merge_source_index,
    update_person_index,
    update_source_index,
    update_statement_index,
)


class CeleryCallBundle:
    def __init__(self, task, model_name) -> None:
        self.task = task
        self.pks = set()
        self.model_name = model_name

    already_called = False

    def add(self, pk):
        self.pks.add(pk)

    def call(self):

        if not self.already_called:
            self.already_called = True
            for pk in self.pks:
                print(f"Creating index task for <{self.model_name} pk={pk}>")
                self.task.delay(pk)
            self.already_called = False
            self.pks = set()


statementCallBundle = CeleryCallBundle(update_statement_index, "Statement")
sourceCallBundle = CeleryCallBundle(update_source_index, "Source")
personCallBundle = CeleryCallBundle(update_person_index, "Person")
factoidCallBundle = CeleryCallBundle(update_factoid_index, "Factoid")
mergePersonCallBundle = CeleryCallBundle(update_merge_person_index, "MergePerson")
mergeSourceCallBundle = CeleryCallBundle(update_merge_source_index, "MergeSource")


def build_uri_from_base(
    instance: Union[Person, Source],
    identifier: str,
    repo: str = None,
):
    uri_template = settings.IPIF_BASE_URI + "/{}ipif/{}/{}"

    if repo:
        return uri_template.format(
            repo + "/",
            instance.__class__.__name__.lower() + "s",
            identifier,
        )
    return uri_template.format(
        "", instance.__class__.__name__.lower() + "s", identifier
    )


def build_extra_uris(instance):
    AUTOCREATED = get_ipif_hub_repo_AUTOCREATED_instance()
    repo_name = instance.ipif_repo.endpoint_slug
    if instance.ipif_repo == AUTOCREATED:
        # Autocreated persons don't need a load of extra identifiers
        return [instance.identifier]
    return [
        instance.identifier,
        build_uri_from_base(instance, instance.identifier),
        build_uri_from_base(instance, instance.local_id, repo=repo_name),
        build_uri_from_base(instance, instance.identifier, repo=repo_name),
    ]


def add_extra_uris(instance):
    uris_to_add = []
    for u in build_extra_uris(instance):

        try:
            uri = URI.objects.get(uri=u)
            uris_to_add.append(uri)
        except URI.DoesNotExist:
            uri = URI(uri=u)
            uri.save()
            uris_to_add.append(uri)
    print("Adding uris", uris_to_add, "to person", instance)
    instance.uris.add(*uris_to_add)


def handle_merge_person_from_person_update(new_person: Person, called_from=None):
    """Receives a Person object"""
    AUTOCREATED = get_ipif_hub_repo_AUTOCREATED_instance()
    if new_person.ipif_repo == AUTOCREATED:
        return

    matching_merge_persons = MergePerson.objects.filter(
        Q(persons__uris__in=new_person.uris.all())
    ).distinct()
    if not matching_merge_persons:
        print(
            "No MP: Creating new MergePerson from person",
            new_person.pk,
            "called from:",
            called_from,
        )
        merge_person = MergePerson(
            createdBy="ipif-hub",
            createdWhen=datetime.date.today(),
            modifiedBy="ipif-hub",
            modifiedWhen=datetime.date.today(),
        )
        merge_person.save()
        merge_person.persons.add(new_person)

    elif len(matching_merge_persons) == 1:
        print(
            "One MP: while adding/modifying person",
            new_person.pk,
            "called from:",
            called_from,
        )
        merge_person = matching_merge_persons.first()
        if new_person not in merge_person.persons.all():
            merge_person.persons.add(new_person)

    elif len(matching_merge_persons) > 1:
        print(
            "More than one MP: person",
            new_person.pk,
            "called from:",
            called_from,
        )
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


def merge_uri_sets(persons: list, results=None) -> Any:
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

    merged_uri_groups: List[list] = merge_uri_sets(uris_to_group)

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


def handle_merge_source_from_source_update(new_source):
    """Receives a Source object"""

    matching_merge_sources = MergeSource.objects.filter(
        sources__uris__in=new_source.uris.all()
    ).distinct()
    if not matching_merge_sources:
        # Create new
        merge_source = MergeSource(
            createdBy="ipif-hub",
            createdWhen=datetime.date.today(),
            modifiedBy="ipif-hub",
            modifiedWhen=datetime.date.today(),
        )
        merge_source.save()
        merge_source.sources.add(new_source)

    elif len(matching_merge_sources) == 1:
        merge_source = matching_merge_sources.first()
        if new_source not in merge_source.sources.all():
            merge_source.sources.add(new_source)

    elif len(matching_merge_sources) > 1:
        all_sources = []
        for merge_source in matching_merge_sources:
            all_sources = [*all_sources, *merge_source.sources.all()]
            merge_source.delete()
        new_merged_source = MergeSource(
            createdBy="ipif-hub",
            createdWhen=datetime.date.today(),
            modifiedBy="ipif-hub",
            modifiedWhen=datetime.date.today(),
        )
        new_merged_source.save()
        new_merged_source.sources.add(*all_sources, new_source)


def handle_delete_source_updating_merge_sources(source_to_delete: Source) -> None:
    """On pre-delete of a source, remove the source's MergeSource
    (delete it later). Find all remaining sources attached to that
    MergeSource, and regroup them by common URIs. Then create
    a new MergeSource for each group, attaching relevant sources.
    """
    old_merge_source = MergeSource.objects.get(sources=source_to_delete)
    remaining_sources = old_merge_source.sources.exclude(pk=source_to_delete.pk)
    uris_to_group = [
        [uri.uri for uri in source.uris.all()] for source in remaining_sources
    ]

    merged_uri_groups: List[list] = merge_uri_sets(uris_to_group)

    for uri_group in merged_uri_groups:
        sources = (
            Source.objects.filter(uris__uri__in=uri_group)
            .exclude(pk=source_to_delete.pk)
            .distinct()
        )
        new_merged_source = MergeSource(
            createdBy="ipif-hub",
            createdWhen=datetime.date.today(),
            modifiedBy="ipif-hub",
            modifiedWhen=datetime.date.today(),
        )
        new_merged_source.save()
        new_merged_source.sources.add(*sources)
    old_merge_source.delete()


@receiver(m2m_changed, sender=MergePerson.persons.through)
def merge_person_m2m_changed(sender, instance, **kwargs):
    print("MergePersonM2M changed", instance.pk)
    mergePersonCallBundle.add(instance.pk)
    transaction.on_commit(mergePersonCallBundle.call)


# Off the top of my head, it should not be necessary to index
# the MergePerson after just a save; the actual change will always
# be on changing the m2m of person
@receiver(post_save, sender=MergePerson)
def index(sender, instance, **kwargs):
    pass


@receiver(m2m_changed, sender=MergeSource.sources.through)
def merge_source_m2m_changed(sender, instance, **kwargs):
    mergeSourceCallBundle.add(instance.pk)
    transaction.on_commit(mergeSourceCallBundle.call)


@receiver(post_save, sender=Factoid)
def factoid_post_save(sender, instance, **kwargs):
    factoidCallBundle.add(instance.pk)
    transaction.on_commit(factoidCallBundle.call)


@receiver(post_save, sender=Person)
def person_post_save(sender, instance: Person, **kwargs):
    # handle_merge_person_from_person_update(instance)
    add_extra_uris(instance)
    # handle_merge_person_from_person_update(instance)

    personCallBundle.add(instance.pk)
    transaction.on_commit(personCallBundle.call)


def split_merge_person_on_uri_delete(instance, kwargs):
    if mp := instance.merge_person.first():
        uris_to_group = [
            [uri.uri for uri in person.uris.all()] for person in mp.persons.all()
        ]
        merged_uri_groups = merge_uri_sets(uris_to_group)
        if len(merged_uri_groups) > 1:
            for uri_group in merged_uri_groups:
                persons = Person.objects.filter(uris__uri__in=uri_group).distinct()
                new_merged_person = MergePerson(
                    createdBy="ipif-hub",
                    createdWhen=datetime.date.today(),
                    modifiedBy="ipif-hub",
                    modifiedWhen=datetime.date.today(),
                )
                new_merged_person.save()
                new_merged_person.persons.add(*persons)

            mp.delete()


def split_merge_source_on_uri_delete(instance, kwargs):
    if ms := instance.merge_source.first():
        uris_to_group = [
            [uri.uri for uri in source.uris.all()] for source in ms.sources.all()
        ]
        merged_uri_groups = merge_uri_sets(uris_to_group)
        if len(merged_uri_groups) > 1:
            for uri_group in merged_uri_groups:
                sources = Source.objects.filter(uris__uri__in=uri_group).distinct()
                new_merged_source = MergeSource(
                    createdBy="ipif-hub",
                    createdWhen=datetime.date.today(),
                    modifiedBy="ipif-hub",
                    modifiedWhen=datetime.date.today(),
                )
                new_merged_source.save()
                new_merged_source.sources.add(*sources)

            ms.delete()


@receiver(m2m_changed, sender=Person.uris.through)
def person_m2m_changed(sender, instance, **kwargs):
    """If a URI is removed from a person, we need to see whether this has broken
    any merge-persons. So, we run the merge_uri_sets to check whether there is more
    than one set: if so, delete the original merge_person and create new ones; otherwise, it's fine."""
    if kwargs["action"] == "post_remove":
        print("--DELETING URI")
        split_merge_person_on_uri_delete(instance, kwargs)

    handle_merge_person_from_person_update(instance, "person_m2m_changed")

    personCallBundle.add(instance.pk)
    transaction.on_commit(personCallBundle.call)


@receiver(pre_delete, sender=Person)
def person_pre_delete(sender, instance, **kwargs):

    handle_delete_person_updating_merge_persons(instance)


@receiver(post_save, sender=Source)
def source_post_save(sender, instance: Source, **kwargs):
    add_extra_uris(instance)

    # handle_merge_source_from_source_update(instance)

    sourceCallBundle.add(instance.pk)
    transaction.on_commit(sourceCallBundle.call)


@receiver(m2m_changed, sender=Source.uris.through)
def source_m2m_changed(sender, instance, **kwargs):
    if kwargs["action"] == "post_remove":
        split_merge_source_on_uri_delete(instance, kwargs)

    handle_merge_source_from_source_update(instance)
    sourceCallBundle.add(instance.pk)
    transaction.on_commit(sourceCallBundle.call)


@receiver(pre_delete, sender=Source)
def source_pre_delete(sender, instance, **kwargs):

    handle_delete_source_updating_merge_sources(instance)


@receiver(post_save, sender=Statement)
def statement_post_save(sender, instance, **kwargs):

    statementCallBundle.add(instance.pk)
    transaction.on_commit(statementCallBundle.call)
