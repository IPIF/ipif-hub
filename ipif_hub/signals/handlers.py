from django.db.models.signals import post_save
from django.dispatch import receiver

from ipif_hub.models import Person, Source, Statement, Factoid

from ipif_hub.tasks import (
    update_factoid_index,
    update_person_index,
    update_source_index,
    update_statement_index,
)


@receiver(post_save, sender=Factoid)
def index_factoid(sender, instance, **kwargs):
    update_factoid_index.delay(instance.pk)


@receiver(post_save, sender=Person)
def index_person(sender, instance, **kwargs):
    update_person_index.delay(instance.pk)


@receiver(post_save, sender=Source)
def index_source(sender, instance, **kwargs):
    update_source_index.delay(instance.pk)


@receiver(post_save, sender=Statement)
def index_statement(sender, instance, **kwargs):
    update_statement_index.delay(instance.pk)
