from celery import chord, group
from django.db import transaction
from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch import receiver

from ipif_hub.models import Factoid, MergePerson, MergeSource, Person, Source, Statement
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
    call_commit,
    update_factoid_index,
    update_merge_person_index,
    update_merge_source_index,
    update_person_index,
    update_source_index,
    update_statement_index,
)


class CeleryCallBundle:
    """Class to bundle together calls to update indexes and call them *once*
    (by using self.already_called flag) after the transaction has completed.

    - Add relevant type with CeleryCallBundle.add_*()
    - To be called inside a transaction.on_commit from a signal

    """

    def __init__(self) -> None:
        self._reset()

    def _reset(self):
        self.factoid_pks_to_index = set()

        self.already_called = False

        self.sources = set()
        self.persons = set()
        self.statements = set()
        self.merge_persons = set()
        self.merge_sources = set()

    def has_tasks(self):
        return any(
            [
                self.sources,
                self.persons,
                self.statements,
                self.merge_persons,
                self.merge_sources,
                self.factoid_pks_to_index,
            ]
        )

    def add_factoid(self, factoid: Factoid):
        self.factoid_pks_to_index.add(factoid.pk)

    def add_source(self, source: Source):
        self.sources.add(source)

    def add_person(self, person: Person):
        self.persons.add(person)

    def add_statement(self, statement: Statement):
        self.statements.add(statement)

    def add_merge_person(self, merge_person: MergePerson):
        self.merge_persons.add(merge_person)

    def add_merge_source(self, merge_source: MergeSource):
        self.merge_sources.add(merge_source)

    def _add_factoids_from_entity_set(self, entity_set):
        entity_set_copy = set(entity_set)
        for entity in entity_set_copy:
            if factoids := entity.factoids.all():
                for factoid in factoids:

                    self.factoid_pks_to_index.add(factoid.pk)
                entity_set.remove(entity)

    def _update_factoids_to_index(self):
        self._add_factoids_from_entity_set(self.persons)
        self._add_factoids_from_entity_set(self.sources)
        self._add_factoids_from_entity_set(self.statements)

        merge_persons_copy = set(self.merge_persons)
        for merge_person in merge_persons_copy:
            if factoids := Factoid.objects.filter(person__merge_person=merge_person):
                for factoid in factoids:
                    # print(f"Creating index update task for <Factoid pk={factoid.pk}>")
                    self.factoid_pks_to_index.add(factoid.pk)
                self.merge_persons.remove(merge_person)

        merge_sources_copy = set(self.merge_sources)
        for merge_source in merge_sources_copy:
            if factoids := Factoid.objects.filter(source__merge_source=merge_source):
                for factoid in factoids:
                    # print(f"Creating index update task for <Factoid pk={factoid.pk}>")
                    self.factoid_pks_to_index.add(factoid.pk)
                self.merge_sources.remove(merge_source)

    def call(self):

        if not self.already_called and self.has_tasks():
            self.already_called = True

            self._update_factoids_to_index()
            tasks = []

            for pk in self.factoid_pks_to_index:
                # print(f"Creating index update task for <Factoid pk={pk}>")
                tasks.append(update_factoid_index.s(pk))

            for source in self.sources:
                # print(f"Creating index update task for <Source pk={source.pk}>")
                tasks.append(update_source_index.s(source.pk))

            for person in self.persons:
                # print(f"Creating index update task for <Person pk={person.pk}>")
                tasks.append(update_person_index.s(person.pk))

            for statement in self.statements:
                # print(f"Creating index update task for <Statement pk={statement.pk}>")
                tasks.append(update_statement_index.s(statement.pk))

            for merge_person in self.merge_persons:
                # print(
                #    f"Creating index update task for <MergePerson pk={merge_person.pk}>"
                # )
                tasks.append(update_merge_person_index.s(merge_person.pk))

            for merge_source in self.merge_sources:
                # print(
                #    f"Creating index update task for <MergeSource pk={merge_source.pk}>"
                # )
                tasks.append(update_merge_source_index.s(merge_source.pk))

            if tasks:
                print(f"Starting {len(tasks)} index update tasks")
                g = group(task for task in tasks)
                chord(g)(group(call_commit.s(immutable=True)))

            self._reset()


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
