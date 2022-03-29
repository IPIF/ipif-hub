from django.db import models


class IpifEntityAbstractBase(models.Model):
    class Meta:
        abstract = True
        unique_together = [["id", "ipif_repo"]]

    id = models.CharField(max_length=300, primary_key=True)
    ipif_repo = models.ForeignKey(
        "IpifRepo", verbose_name="IPIF Repository", on_delete=models.CASCADE
    )

    createdBy = models.CharField(max_length=300)
    createdWhen = models.DateField()
    modifiedBy = models.CharField(max_length=300)
    modifiedWhen = models.DateField()

    hubIngestedWhen = models.DateTimeField(auto_now_add=True)
    hubModifiedWhen = models.DateTimeField(auto_now=True)

    @property
    def qualified_id(self):
        """Returns the full IPIF-compliant URL version of the entity"""
        url = (
            self.ipif_repo.uri[:-1]
            if self.ipif_repo.uri.endswith("/")
            else self.ipif_repo.uri
        )
        entity_type = f"{type(self).__name__.lower()}s"
        return f"{url}/{entity_type}/{self.id}"


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
    id = models.CharField(max_length=300, unique=True, primary_key=True)
    uri = models.URLField()


class Place(models.Model):
    uri = models.URLField(primary_key=True)
    label = models.CharField(max_length=300, null=True)

    def __str__(self):
        return f"{self.label} ({self.uri})"


class URI(models.Model):
    uri = models.URLField()

    def __str__(self):
        return self.uri
