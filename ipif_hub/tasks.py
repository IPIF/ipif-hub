import datetime
import sys
from io import StringIO

from celery import shared_task
from celery.utils.log import get_task_logger

from ipif_hub.management.utils.ingest_data import ingest_data
from ipif_hub.models import (
    Factoid,
    IngestionJob,
    MergePerson,
    MergeSource,
    Person,
    Source,
    Statement,
)
from ipif_hub.search_indexes import (
    FactoidIndex,
    MergePersonIndex,
    MergeSourceIndex,
    PersonIndex,
    SourceIndex,
    StatementIndex,
)

logger = get_task_logger(__name__)


@shared_task(ignore_result=True)
def update_merge_person_index(instance_pk):
    merge_person_searches = MergePersonIndex.objects.filter(django_id=instance_pk)
    for merge_person_search in merge_person_searches:
        merge_person_search.searchindex.update_object(
            MergePerson.objects.get(pk=instance_pk)
        )


@shared_task(ignore_result=True)
def update_merge_source_index(instance_pk):
    merge_source_searches = MergeSourceIndex.objects.filter(django_id=instance_pk)
    for merge_source_search in merge_source_searches:
        merge_source_search.searchindex.update_object(
            MergeSource.objects.get(pk=instance_pk)
        )


@shared_task(ignore_result=True)
def update_factoid_index(instance_pk):
    try:

        factoid_searches = FactoidIndex.objects.filter(django_id=instance_pk)
        for factoid_search in factoid_searches:
            factoid_search.searchindex.update_object(
                Factoid.objects.get(pk=instance_pk)
            )

        person = Factoid.objects.get(pk=instance_pk).person

        person_searches = PersonIndex.objects.filter(django_id=person.pk)
        for person_search in person_searches:
            person_search.searchindex.update_object(person)

        if merge_person := person.merge_person.first():
            update_merge_person_index.delay(merge_person.pk)

        source = Factoid.objects.get(pk=instance_pk).source
        source_searches = SourceIndex.objects.filter(django_id=source.pk)
        for source_search in source_searches:
            source_search.searchindex.update_object(source)

        if merge_source := source.merge_source.first():
            update_merge_source_index.delay(merge_source.pk)

        statements = Factoid.objects.get(pk=instance_pk).statements.all()
        for statement in statements:
            statement_searches = StatementIndex.objects.filter(django_id=statement.pk)
            for statement_search in statement_searches:
                statement_search.searchindex.update_object(statement)
    except Factoid.DoesNotExist:
        pass


@shared_task(ignore_result=True)
def update_person_index(instance_pk):

    person = Person.objects.get(pk=instance_pk)

    for factoid in person.factoids.all():
        update_factoid_index.delay(factoid.pk)

    # if merge_person := person.merge_person.first():
    #    update_merge_person_index(merge_person.pk)


@shared_task(ignore_result=True)
def update_source_index(instance_pk):
    source = Source.objects.get(pk=instance_pk)

    for factoid in source.factoids.all():
        update_factoid_index.delay(factoid.pk)


@shared_task(ignore_result=True)
def update_statement_index(instance_pk):

    statement = Statement.objects.get(pk=instance_pk)

    for factoid in statement.factoids.all():
        update_factoid_index.delay(factoid.pk)


class Capturing(list):
    """Grabs stdout and returns results as an array"""

    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio  # free up some memory
        sys.stdout = self._stdout


@shared_task(ignore_result=True)
def ingest_json_data_task(repo_id, data, job_id=None):
    logger.info("ingesting data")
    job = IngestionJob.objects.get(pk=job_id)

    job.job_status = "running"
    job.save()
    with Capturing() as output:
        ingest_data(repo_id, data)

    job.is_complete = True
    job.job_output = output
    job.job_status = "successful"
    job.end_datetime = datetime.datetime.now()
    job.save()

    """ # Don't need this any more
    send_mail(
        subject="Upload complete",
        message=json.dumps(output),
        recipient_list=["oculardexterity@gmail.com"],
        from_email="ipif@hub.com",
    )
    """
