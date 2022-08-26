from datetime import datetime
from typing import Set, Union
from uuid import uuid4

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from django.forms import ValidationError


class IpifEntityAbstractBase(models.Model):
    class Meta:
        abstract = True
        unique_together = [["local_id", "ipif_repo", "identifier"]]

    id: models.UUIDField = models.UUIDField(
        primary_key=True, editable=False, default=uuid4, db_index=True
    )

    # In change from previous version, the URL-as-pk idea has been shelved.
    # Instead, a separate identifier field exists — this should be treated as the main
    # way to look things up... but also useful as it allows canonical URIs to be used
    # as identifiers. If this were the pk, two projects could not use the same URI.
    # Consequently, we now need to qualify all lookups with the repo id!
    identifier: models.URLField = models.URLField(
        default="http://noneset.com", editable=False, db_index=True
    )

    local_id: models.CharField = models.CharField(
        max_length=50, blank=True, db_index=True
    )
    ipif_repo: models.ForeignKey = models.ForeignKey(
        "IpifRepo",
        verbose_name="IPIF Repository",
        on_delete=models.CASCADE,
        db_index=True,
    )
    label: models.CharField = models.CharField(max_length=300, default="", blank=True)

    createdBy: models.CharField = models.CharField(max_length=300)
    createdWhen: models.DateField = models.DateField()
    modifiedBy: models.CharField = models.CharField(max_length=300)
    modifiedWhen: models.DateField = models.DateField()

    hubIngestedWhen: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    hubModifiedWhen: models.DateTimeField = models.DateTimeField(auto_now=True)

    inputContentHash: models.CharField = models.CharField(max_length=60, default="")

    def build_uri_id_from_slug(self, id: str) -> str:
        """Returns the full IPIF-compliant URL version of the entity"""
        try:
            validator = URLValidator()
            validator(id)
            return id
        except ValidationError:
            pass

        url = (
            self.ipif_repo.endpoint_uri[:-1]
            if self.ipif_repo.endpoint_uri.endswith("/")
            else self.ipif_repo.endpoint_uri
        )
        entity_type = f"{type(self).__name__.lower()}s"
        return f"{url}/{entity_type}/{id}"

    def save(self, *args, **kwargs) -> None:
        if not self.identifier or self.identifier == "http://noneset.com":
            self.identifier = self.build_uri_id_from_slug(self.local_id)
        super().save(*args, **kwargs)


class URI(models.Model):
    uri: models.URLField = models.URLField(db_index=True)

    def __str__(self):
        return self.uri


class AbstractMergeEntity(models.Model):
    class Meta:
        abstract = True

    id: models.UUIDField = models.UUIDField(
        primary_key=True, editable=False, default=uuid4, db_index=True
    )
    createdBy: models.CharField = models.CharField(max_length=300)
    createdWhen: models.DateField = models.DateField()
    modifiedBy: models.CharField = models.CharField(max_length=300)
    modifiedWhen: models.DateField = models.DateField()

    @property
    def uri_set(self) -> Set:
        return {uri.uri for uri in self.uris.distinct()}

    @property
    def uris(self):
        raise NotImplementedError


class MergePerson(AbstractMergeEntity):

    persons = models.ManyToManyField(
        "Person",
        related_name="merge_person",
    )

    @property
    def uris(self):
        uris = URI.objects.filter(persons__in=self.persons.all()).distinct()
        return uris


class MergeSource(AbstractMergeEntity):
    sources = models.ManyToManyField(
        "Source",
        related_name="merge_source",
    )

    @property
    def uris(self):
        uris = URI.objects.filter(sources__in=self.sources.all()).distinct()
        return uris


class Factoid(IpifEntityAbstractBase):

    person = models.ForeignKey(
        "Person",
        on_delete=models.CASCADE,
        related_query_name="factoids",
        related_name="factoids",
    )
    source = models.ForeignKey(
        "Source",
        on_delete=models.CASCADE,
        related_query_name="factoids",
        related_name="factoids",
    )
    statements = models.ManyToManyField(
        "Statement",
        verbose_name="statements",
        related_query_name="factoids",
        related_name="factoids",
    )


class Person(IpifEntityAbstractBase):

    uris = models.ManyToManyField("URI", related_name="persons", blank=True)

    def __str__(self) -> str:
        uri_string = (
            f" ({', '.join(uri.uri for uri in self.uris.all())})"
            if self.uris.exists()
            else ""
        )
        return f"{self.label}{uri_string}"


class Statement(IpifEntityAbstractBase):

    statementType_uri: models.URLField = models.URLField(
        blank=True, null=True, db_index=True
    )
    statementType_label: models.CharField = models.CharField(
        max_length=300, blank=True, null=True, db_index=True
    )

    name = models.CharField(max_length=300, blank=True, null=True, db_index=True)

    role_uri = models.URLField(blank=True, null=True, db_index=True)
    role_label = models.CharField(max_length=300, blank=True, null=True, db_index=True)

    date_sortdate = models.DateField(blank=True, null=True, db_index=True)
    date_label = models.CharField(max_length=100, blank=True, null=True, db_index=True)

    places = models.ManyToManyField("Place", blank=True)

    relatesToPerson = models.ManyToManyField(
        "Person", verbose_name="relatedToPerson", blank=True
    )

    memberOf_uri = models.URLField(blank=True, null=True, db_index=True)
    memberOf_label = models.CharField(
        max_length=300, blank=True, null=True, db_index=True
    )

    statementText = models.CharField(
        max_length=1000, blank=True, null=True, db_index=True
    )


class Source(IpifEntityAbstractBase):

    uris = models.ManyToManyField("URI", related_name="sources", blank=True)

    def __str__(self) -> str:
        uri_string = (
            f" ({', '.join(uri.uri for uri in self.uris.all())})"
            if self.uris.exists()
            else ""
        )
        return f"{self.label}{uri_string}"


class Place(models.Model):
    uri = models.URLField(primary_key=True, db_index=True)
    label = models.CharField(max_length=300, null=True, db_index=True)

    def __str__(self):
        return f"{self.label} ({self.uri})"


class IpifRepo(models.Model):
    owners = models.ManyToManyField(to=User)

    endpoint_slug = models.CharField(
        max_length=20,
        primary_key=True,
        db_index=True,
        blank=False,
        editable=False,
        null=False,
        default=None,
    )
    endpoint_name = models.CharField(max_length=30, default="")

    endpoint_uri = models.URLField(db_index=True)
    refresh_frequency = models.CharField(
        max_length=10,
        choices=(("daily", "daily"), ("weekly", "weekly"), ("never", "never")),
        default="never",
    )
    refresh_time = models.TimeField(null=True)
    endpoint_is_ipif = models.BooleanField(default=False)

    description = models.TextField()
    provider = models.CharField(max_length=100, default="", blank=True)

    repo_active = models.BooleanField(default=False)

    batch_is_canonical = models.BooleanField(default=True)
    rest_write_enabled = models.BooleanField(default=False)


class IngestionJob(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    is_complete = models.BooleanField(default=False)
    start_datetime = models.DateTimeField(default=datetime.now)
    end_datetime = models.DateTimeField(default=None, null=True, blank=True)
    job_type = models.CharField(
        max_length=20, choices=(("file_batch_upload", "file batch upload"),)
    )
    ipif_repo = models.ForeignKey("IpifRepo", on_delete=models.CASCADE)

    job_status = models.CharField(max_length=20, default="created")
    job_output = models.TextField(default="")

    def mark_as_complete(self):
        self.end_datetime = datetime.now()
        self.is_complete = True

    @property
    def job_duration(self) -> Union[datetime, None]:
        if self.is_complete:
            return self.end_datetime - self.start_datetime
        return None


def get_ipif_hub_repo_AUTOCREATED_instance() -> IpifRepo:
    try:
        ipif_hub_repo_AUTOCREATED = IpifRepo.objects.get(
            endpoint_slug="IPIFHUB_AUTOCREATED"
        )
    except IpifRepo.DoesNotExist:
        ipif_hub_repo_AUTOCREATED = IpifRepo(
            endpoint_name="IPIFHUB_AUTOCREATED",
            endpoint_slug="IPIFHUB_AUTOCREATED",
            endpoint_uri="http://IPIFHUB_AUTOCREATED",
            refresh_frequency="never",
            refresh_time="00:00",
            endpoint_is_ipif=False,
        )
        ipif_hub_repo_AUTOCREATED.save()

    return ipif_hub_repo_AUTOCREATED
