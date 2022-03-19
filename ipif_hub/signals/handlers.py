from django.db.models.signals import pre_save
from django.dispatch import receiver

from ipif_hub.models import Person, Source, Statement, Factoid
from ipif_hub.serializers import (
    FactoidSerializer,
    PersonSerializer,
    SourceSerializer,
    StatementSerializer,
)


"""
Let's pre-serialize everything and slap that in the database too!
"""


@receiver(pre_save, sender=Person)
def pre_serialize_person(sender, instance, **kwargs):
    instance.pre_serialized = PersonSerializer(instance).data


@receiver(pre_save, sender=Source)
def pre_serialize_source(sender, instance, **kwargs):
    instance.pre_serialized = SourceSerializer(instance).data


@receiver(pre_save, sender=Factoid)
def pre_serialize_factoid(sender, instance, **kwargs):
    instance.pre_serialized = FactoidSerializer(instance).data


@receiver(pre_save, sender=Statement)
def pre_serialize_factoid(sender, instance, **kwargs):
    instance.pre_serialized = StatementSerializer(instance).data
