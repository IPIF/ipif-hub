from django.db.models.signals import pre_save, m2m_changed
from django.dispatch import receiver

from ipif_hub.models import Person, Source, Statement, Factoid
from ipif_hub.serializers import (
    FactoidSerializer,
    PersonSerializer,
    SourceSerializer,
    StatementSerializer,
)
from ipif_hub.search_indexes import PersonIndex

"""
Let's pre-serialize everything and slap that in the database too!
"""


"""
@receiver(pre_save, sender=Factoid)
def pre_serialize_factoid(sender, instance, **kwargs):

    instance.pre_serialized = FactoidSerializer(instance).data

    instance.person.save()

    instance.source.save()

    for statement in instance.statement.all():

        statement.save()
"""


@receiver(pre_save, sender=Person)
def pre_serialize_person(sender, instance, **kwargs):

    ss = PersonIndex.objects.filter(django_id=instance.pk)
    for s in ss:
        s.searchindex.update_object(instance)


"""
@receiver(pre_save, sender=Source)
def pre_serialize_source(sender, instance, **kwargs):

    instance.pre_serialized = SourceSerializer(instance).data

    for factoid in instance.factoids.all():

        factoid.save()


@receiver(pre_save, sender=Statement)
def pre_serialize_statement(sender, instance, **kwargs):

    instance.pre_serialized = StatementSerializer(instance).data

    for factoid in instance.factoid.all():

        factoid.save()
"""
