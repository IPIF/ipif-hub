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

AUTOCREATED = get_ipif_hub_repo_AUTOCREATED_instance()


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
    repo_name = instance.ipif_repo.endpoint_slug
    return [
        instance.identifier,
        build_uri_from_base(instance, instance.identifier),
        build_uri_from_base(instance, instance.local_id, repo=repo_name),
        build_uri_from_base(instance, instance.identifier, repo=repo_name),
    ]


def add_extra_uris(instance):
    for u in build_extra_uris(instance):

        try:
            uri = URI.objects.get(uri=u)
            instance.uris.add(uri)
        except URI.DoesNotExist:
            uri = URI(uri=u)
            uri.save()
            instance.uris.add(uri)


def handle_merge_person_from_person_update(new_person: Person):
    """Receives a Person object"""

    if new_person.ipif_repo == AUTOCREATED:
        return

    matching_merge_persons = MergePerson.objects.filter(
        Q(persons__uris__in=new_person.uris.all())
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
    )
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

    transaction.on_commit(lambda: update_merge_person_index(instance.pk))


# Off the top of my head, it should not be necessary to index
# the MergePerson after just a save; the actual change will always
# be on changing the m2m of person
@receiver(post_save, sender=MergePerson)
def index(sender, instance, **kwargs):
    pass


@receiver(m2m_changed, sender=MergeSource.sources.through)
def merge_source_m2m_changed(sender, instance, **kwargs):
    # print("MP_m2mchanged SOURCE CALLED")
    transaction.on_commit(lambda: update_merge_source_index(instance.pk))


@receiver(post_save, sender=Factoid)
def factoid_post_save(sender, instance, **kwargs):

    transaction.on_commit(lambda: update_factoid_index.delay(instance.pk))


@receiver(post_save, sender=Person)
def person_post_save(sender, instance: Person, **kwargs):
    # handle_merge_person_from_person_update(instance)

    add_extra_uris(instance)

    handle_merge_person_from_person_update(instance)
    transaction.on_commit(lambda: update_person_index.delay(instance.pk))


@receiver(m2m_changed, sender=Person.uris.through)
def person_m2m_changed(sender, instance, **kwargs):
    """TODO: If a URI is removed from a person, we need to see whether this has broken
    any merge-persons. So, we run the merge_uri_sets to check whether there is more
    than one set: if so, delete the original merge_person and create new ones; otherwise, it's fine."""

    handle_merge_person_from_person_update(instance)
    transaction.on_commit(lambda: update_person_index.delay(instance.pk))


@receiver(pre_delete, sender=Person)
def person_pre_delete(sender, instance, **kwargs):

    handle_delete_person_updating_merge_persons(instance)


@receiver(post_save, sender=Source)
def source_post_save(sender, instance: Source, **kwargs):
    add_extra_uris(instance)

    handle_merge_source_from_source_update(instance)
    transaction.on_commit(lambda: update_source_index.delay(instance.pk))


@receiver(m2m_changed, sender=Source.uris.through)
def source_m2m_changed(sender, instance, **kwargs):
    """TODO: If a URI is removed from a source, we need to see whether this has broken
    any merge-sources. So, we run the merge_uri_sets to check whether there is more
    than one set: if so, delete the original merge_source and create new ones; otherwise, it's fine."""

    handle_merge_source_from_source_update(instance)
    transaction.on_commit(lambda: update_source_index.delay(instance.pk))


@receiver(pre_delete, sender=Source)
def source_pre_delete(sender, instance, **kwargs):

    handle_delete_source_updating_merge_sources(instance)


@receiver(post_save, sender=Statement)
def statement_post_save(sender, instance, **kwargs):
    transaction.on_commit(lambda: update_statement_index.delay(instance.pk))
