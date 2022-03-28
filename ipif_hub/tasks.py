from celery import shared_task
from ipif_hub.search_indexes import FactoidIndex, PersonIndex, SourceIndex
from ipif_hub.models import Factoid, Person, Source
from celery.utils.log import get_task_logger


logger = get_task_logger(__name__)


@shared_task
def update_factoid_index(instance_pk):
    factoid_searches = FactoidIndex.objects.filter(django_id=instance_pk)
    for factoid_search in factoid_searches:
        factoid_search.searchindex.update_object(Factoid.objects.get(pk=instance_pk))

    person = Factoid.objects.get(pk=instance_pk).person
    person_searches = PersonIndex.objects.filter(django_id=person.pk)
    for person_search in person_searches:
        person_search.searchindex.update_object(person)

    source = Factoid.objects.get(pk=instance_pk).source
    source_searches = SourceIndex.objects.filter(django_id=source.pk)
    for source_search in source_searches:
        source_search.searchindex.update_object(source)


@shared_task
def update_person_index(instance_pk):
    person = Person.objects.get(pk=instance_pk)

    for factoid in person.factoids.all():
        update_factoid_index.delay(factoid.pk)


@shared_task
def update_source_index(instance_pk):
    source = Source.objects.get(pk=instance_pk)

    for factoid in source.factoids.all():
        update_factoid_index.delay(factoid.pk)
