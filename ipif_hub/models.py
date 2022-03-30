from django.db import models
from django.core.validators import URLValidator
from django.forms import ValidationError


class IpifEntityAbstractBase(models.Model):
    class Meta:
        abstract = True
        # unique_together = [["local_id", "ipif_repo"]]

    id = models.URLField(primary_key=True, default="http://noneset.com", editable=False)
    local_id = models.CharField(max_length=50, blank=True)
    ipif_repo = models.ForeignKey(
        "IpifRepo", verbose_name="IPIF Repository", on_delete=models.CASCADE
    )

    createdBy = models.CharField(max_length=300)
    createdWhen = models.DateField()
    modifiedBy = models.CharField(max_length=300)
    modifiedWhen = models.DateField()

    hubIngestedWhen = models.DateTimeField(auto_now_add=True)
    hubModifiedWhen = models.DateTimeField(auto_now=True)

    def build_uri_id_from_slug(self, id):
        """Returns the full IPIF-compliant URL version of the entity"""
        url = (
            self.ipif_repo.endpoint_url[:-1]
            if self.ipif_repo.endpoint_url.endswith("/")
            else self.ipif_repo.endpoint_url
        )
        entity_type = f"{type(self).__name__.lower()}s"
        return f"{url}/{entity_type}/{id}"

    def save(self, *args, **kwargs):
        self.id = self.build_uri_id_from_slug(self.local_id)
        super().save(*args, **kwargs)


class Factoid(IpifEntityAbstractBase):
    label = models.CharField(max_length=300, default="")

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
    pre_serialized = models.JSONField(default=dict, blank=True)


class Person(IpifEntityAbstractBase):
    label = models.CharField(max_length=300, default="")
    uris = models.ManyToManyField("URI", blank=True)
    pre_serialized = models.JSONField(default=dict, blank=True)

    def __str__(self):
        uri_string = (
            f" ({', '.join(uri.uri for uri in self.uris.all())})"
            if self.uris.exists()
            else ""
        )
        return f"{self.label}{uri_string}"


class Statement(IpifEntityAbstractBase):
    label = models.CharField(max_length=300, default="")

    pre_serialized = models.JSONField(default=dict, blank=True)

    statementType_uri = models.URLField(blank=True, null=True)
    statementType_label = models.CharField(max_length=300, blank=True, null=True)

    name = models.CharField(max_length=300, blank=True, null=True)

    role_uri = models.URLField(blank=True, null=True)
    role_label = models.CharField(max_length=300, blank=True, null=True)

    date_sortdate = models.DateField(blank=True, null=True)
    date_label = models.CharField(max_length=100, blank=True, null=True)

    places = models.ManyToManyField("Place", blank=True)

    relatesToPerson = models.ManyToManyField(
        "Person", verbose_name="relatedToPerson", blank=True
    )

    memberOf_uri = models.URLField(blank=True, null=True)
    memberOf_label = models.CharField(max_length=300, blank=True, null=True)

    statementText = models.CharField(max_length=1000, blank=True, null=True)


class Source(IpifEntityAbstractBase):
    label = models.CharField(max_length=300, default="")
    uris = models.ManyToManyField("URI", blank=True)
    pre_serialized = models.JSONField(default=dict, blank=True)

    def __str__(self):
        uri_string = (
            f" ({', '.join(uri.uri for uri in self.uris.all())})"
            if self.uris.exists()
            else ""
        )
        return f"{self.label}{uri_string}"


class IpifRepo(models.Model):
    endpoint_slug = models.CharField(max_length=20, primary_key=True)
    endpoint_url = models.URLField()
    refresh_frequency = models.CharField(
        max_length=10, choices=(("daily", "daily"), ("weekly", "weekly"))
    )
    refresh_time = models.TimeField()
    endpoint_is_ipif = models.BooleanField()


class Place(models.Model):
    uri = models.URLField(primary_key=True)
    label = models.CharField(max_length=300, null=True)

    def __str__(self):
        return f"{self.label} ({self.uri})"


class URI(models.Model):
    uri = models.URLField()

    def __str__(self):
        return self.uri
