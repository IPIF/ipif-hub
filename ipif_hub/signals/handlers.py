import datetime
from heapq import merge

from django.db import transaction
from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch import receiver

from ipif_hub.models import (
    Factoid,
    MergePerson,
    MergeSource,
    Person,
    Source,
    Statement,
    get_ipif_hub_repo_AUTOCREATED_instance,
)
from ipif_hub.signals.handler_utils import (
    add_extra_uris,
    handle_delete_person_updating_merge_persons,
    handle_delete_source_updating_merge_sources,
    handle_merge_person_from_person_update,
    handle_merge_source_from_source_update,
    split_merge_person_on_uri_delete,
    split_merge_source_on_uri_delete,
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
    def __init__(self) -> None:
        self.pks = set()

    already_called = False

    def add_factoid(self, factoid: Factoid):
        self.pks.add(factoid.pk)

    def add_source(self, source: Source):
        for factoid in source.factoids.all():
            self.pks.add(factoid.pk)

    def add_person(self, person: Person):
        for factoid in person.factoids.all():
            self.pks.add(factoid.pk)

    def add_statement(self, statement: Statement):
        for factoid in statement.factoids.all():
            self.pks.add(factoid.pk)

    def add_merge_person(self, merge_person: MergePerson):
        # print("adding MP to index refresh")
        for person in merge_person.persons.all():
            print("adding merge person", merge_person, person)
            self.add_person(person)

    def add_merge_source(self, merge_source: MergeSource):
        for source in merge_source.sources.all():
            self.add_source(source)

    def call(self):
        if not self.already_called:
            self.already_called = True
            for pk in self.pks:
                print(f"Creating index task for <Factoid pk={pk}>")
                update_factoid_index.delay(pk)
            self.already_called = False
            self.pks = set()


celeryCallBundle = CeleryCallBundle()


@receiver(m2m_changed, sender=MergePerson.persons.through)
def merge_person_m2m_changed(sender, instance, **kwargs):
    celeryCallBundle.add_merge_person(instance)
    transaction.on_commit(celeryCallBundle.call)


# Off the top of my head, it should not be necessary to index
# the MergePerson after just a save; the actual change will always
# be on changing the m2m of person
@receiver(post_save, sender=MergePerson)
def index(sender, instance, **kwargs):
    pass


@receiver(m2m_changed, sender=MergeSource.sources.through)
def merge_source_m2m_changed(sender, instance, **kwargs):
    celeryCallBundle.add_merge_source(instance)
    transaction.on_commit(celeryCallBundle.call)


@receiver(post_save, sender=Factoid)
def factoid_post_save(sender, instance, **kwargs):
    celeryCallBundle.add_factoid(instance)
    transaction.on_commit(celeryCallBundle.call)


@receiver(post_save, sender=Person)
def person_post_save(sender, instance: Person, **kwargs):
    # handle_merge_person_from_person_update(instance)
    add_extra_uris(instance)
    # handle_merge_person_from_person_update(instance)

    celeryCallBundle.add_person(instance)
    transaction.on_commit(celeryCallBundle.call)


@receiver(m2m_changed, sender=Person.uris.through)
def person_m2m_changed(sender, instance, **kwargs):
    """If a URI is removed from a person, we need to see whether this has broken
    any merge-persons. So, we run the merge_uri_sets to check whether there is more
    than one set: if so, delete the original merge_person and create new ones; otherwise, it's fine."""
    if kwargs["action"] == "post_remove":

        split_merge_person_on_uri_delete(instance, kwargs)

    handle_merge_person_from_person_update(instance, "person_m2m_changed")

    celeryCallBundle.add_person(instance)
    transaction.on_commit(celeryCallBundle.call)


@receiver(pre_delete, sender=Person)
def person_pre_delete(sender, instance, **kwargs):

    handle_delete_person_updating_merge_persons(instance)


@receiver(post_save, sender=Source)
def source_post_save(sender, instance: Source, **kwargs):
    add_extra_uris(instance)

    # handle_merge_source_from_source_update(instance)

    celeryCallBundle.add_source(instance)
    transaction.on_commit(celeryCallBundle.call)


@receiver(m2m_changed, sender=Source.uris.through)
def source_m2m_changed(sender, instance, **kwargs):
    if kwargs["action"] == "post_remove":
        split_merge_source_on_uri_delete(instance, kwargs)

    handle_merge_source_from_source_update(instance)
    celeryCallBundle.add_source(instance)
    transaction.on_commit(celeryCallBundle.call)


@receiver(pre_delete, sender=Source)
def source_pre_delete(sender, instance, **kwargs):

    handle_delete_source_updating_merge_sources(instance)


@receiver(post_save, sender=Statement)
def statement_post_save(sender, instance, **kwargs):

    celeryCallBundle.add_statement(instance)
    transaction.on_commit(celeryCallBundle.call)
