from django.db import models
from django.core.validators import URLValidator
from django.forms import ValidationError


class IpifEntityAbstractBase(models.Model):
    class Meta:
        abstract = True
        unique_together = [["local_id", "ipif_repo"]]

    # This setting id like this is a HACK (?)
    # Idea being, user provides a local id, which we make global by prefixing the repo id
    # then save this as PK —— see the save() method below
    id = models.URLField(
        primary_key=True, default="http://noneset.com", editable=False, db_index=True
    )

    local_id = models.CharField(max_length=50, blank=True)
    ipif_repo = models.ForeignKey(
        "IpifRepo",
        verbose_name="IPIF Repository",
        on_delete=models.CASCADE,
        db_index=True,
    )
    label = models.CharField(max_length=300, default="", blank=True)

    createdBy = models.CharField(max_length=300)
    createdWhen = models.DateField()
    modifiedBy = models.CharField(max_length=300)
    modifiedWhen = models.DateField()

    hubIngestedWhen = models.DateTimeField(auto_now_add=True)
    hubModifiedWhen = models.DateTimeField(auto_now=True)

    inputContentHash = models.CharField(max_length=60, default="")

    def build_uri_id_from_slug(self, id):
        """Returns the full IPIF-compliant URL version of the entity"""
        url = (
            self.ipif_repo.endpoint_uri[:-1]
            if self.ipif_repo.endpoint_uri.endswith("/")
            else self.ipif_repo.endpoint_uri
        )
        entity_type = f"{type(self).__name__.lower()}s"
        return f"{url}/{entity_type}/{id}"

    def save(self, *args, **kwargs):
        if not self.id or self.id == "http://noneset.com":
            print("no id set... generating", self)
            print(self.build_uri_id_from_slug(self.local_id))
            self.id = self.build_uri_id_from_slug(self.local_id)
        super().save(*args, **kwargs)


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
    statement = models.ManyToManyField(
        "Statement",
        verbose_name="statements",
        related_query_name="factoids",
        related_name="factoids",
    )


class Person(IpifEntityAbstractBase):

    uris = models.ManyToManyField("URI", blank=True)

    def __str__(self):
        uri_string = (
            f" ({', '.join(uri.uri for uri in self.uris.all())})"
            if self.uris.exists()
            else ""
        )
        return f"{self.label}{uri_string}"


class Statement(IpifEntityAbstractBase):

    statementType_uri = models.URLField(blank=True, null=True, db_index=True)
    statementType_label = models.CharField(
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

    uris = models.ManyToManyField("URI", blank=True)

    def __str__(self):
        uri_string = (
            f" ({', '.join(uri.uri for uri in self.uris.all())})"
            if self.uris.exists()
            else ""
        )
        return f"{self.label}{uri_string}"


class IpifRepo(models.Model):
    endpoint_name = models.CharField(max_length=30, default="")
    endpoint_slug = models.CharField(max_length=20, primary_key=True, db_index=True)
    endpoint_uri = models.URLField(db_index=True)
    refresh_frequency = models.CharField(
        max_length=10,
        choices=(("daily", "daily"), ("weekly", "weekly"), ("never", "never")),
    )
    refresh_time = models.TimeField()
    endpoint_is_ipif = models.BooleanField()


class Place(models.Model):
    uri = models.URLField(primary_key=True, db_index=True)
    label = models.CharField(max_length=300, null=True, db_index=True)

    def __str__(self):
        return f"{self.label} ({self.uri})"


class URI(models.Model):
    uri = models.URLField(db_index=True)

    def __str__(self):
        return self.uri


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
