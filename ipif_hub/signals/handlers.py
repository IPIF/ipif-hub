from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver


from ipif_hub.models import Person, Source, Statement, Factoid
from ipif_hub.serializers import (
    FactoidSerializer,
    PersonSerializer,
    SourceSerializer,
    StatementSerializer,
)
from ipif_hub.search_indexes import PersonIndex

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
    if instance.ipif_repo.endpoint_slug != "IPIFHUB_AUTOCREATED":
        update_person_index.delay(instance.pk)
    else:
        print("autocreated... skipping")


@receiver(post_save, sender=Source)
def index_source(sender, instance, **kwargs):
    update_source_index.delay(instance.pk)


@receiver(post_save, sender=Statement)
def index_statement(sender, instance, **kwargs):
    update_statement_index.delay(instance.pk)
