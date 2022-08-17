import datetime

from django.db.models.signals import post_save, m2m_changed
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


@receiver(m2m_changed, sender=MergePerson.persons.through)
def merge_person_m2m_changed(sender, instance, **kwargs):
    # print("MP_m2mchanged PERSON CALLED")
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


@receiver(post_save, sender=Source)
def source_post_save(sender, instance, **kwargs):
    transaction.on_commit(lambda: update_source_index.delay(instance.pk))


@receiver(post_save, sender=Statement)
def statement_post_save(sender, instance, **kwargs):
    transaction.on_commit(lambda: update_statement_index.delay(instance.pk))
