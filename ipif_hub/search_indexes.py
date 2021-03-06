import datetime
import json
import os
from re import L

from haystack import indexes

from ipif_hub.serializers import (
    FactoidSerializer,
    PersonSerializer,
    SourceSerializer,
    StatementSerializer,
)

from .models import Person, Source, Factoid, Statement


TEMPLATE_DIR = os.path.join(
    os.path.dirname(__file__), "templates", "search", "indexes", "ipif_hub"
)


def get_template(file_name):
    return os.path.join(TEMPLATE_DIR, file_name)


"""
Fields to sort by:

✅ personId
✅ p
✅ factoidId
✅ f
✅ statementId
✅ st
✅ sourceId
✅ s


✅ statementText

✅ relatesToPerson
✅ memberOf
✅ role
✅ name
✅ from
✅ to
place

"""
SORT_LAST = "ZZZZZZZZ"
SORT_DATE_LAST = datetime.datetime(2060, 1, 1)


class BaseIndex(indexes.SearchIndex):
    local_id = indexes.CharField(model_attr="local_id")
    ipif_repo_id = indexes.CharField()
    ipif_repo_slug = indexes.CharField()
    ipif_type = indexes.CharField()
    label = indexes.CharField(model_attr="label")
    hubModifiedWhen = indexes.DateTimeField(model_attr="hubModifiedWhen")
    pre_serialized = indexes.CharField()

    sort_createdBy = indexes.CharField(model_attr="createdBy")
    sort_createdWhen = indexes.DateField(model_attr="createdWhen")
    sort_modifiedBy = indexes.CharField(model_attr="modifiedBy")
    sort_modifiedWhen = indexes.DateField(model_attr="modifiedWhen")
    sort_personId = indexes.CharField()
    sort_statementId = indexes.CharField()
    sort_sourceId = indexes.CharField()
    sort_factoidId = indexes.CharField()
    sort_statementText = indexes.CharField()
    sort_relatesToPerson = indexes.CharField()
    sort_memberOf = indexes.CharField()
    sort_role = indexes.CharField()
    sort_name = indexes.CharField()
    sort_from = indexes.DateTimeField()
    sort_to = indexes.DateTimeField()
    sort_place = indexes.CharField()

    ## REMOVE default TEXT
    text = indexes.CharField(document=True, use_template=True)

    def prepare_ipif_repo_id(self, inst):
        return inst.ipif_repo.endpoint_uri

    def prepare_ipif_repo_slug(self, inst):
        return inst.ipif_repo.endpoint_slug

    def prepare_ipif_type(self, inst):
        return self.get_model().__name__.lower()

    def prepare_pre_serialized(self, inst):
        serializer = globals()[f"{self.get_model().__name__}Serializer"]
        return json.dumps(serializer(inst).data)

    def prepare_uris(self, inst):
        values = []
        for uri in inst.uris.all():
            values.append(uri.uri)
        return values

    def prepare_sort_personId(self, inst):
        if self.get_model().__name__ == "Factoid":
            return inst.person.local_id
        if factoid := inst.factoids.first():
            return factoid.person.local_id
        return SORT_LAST

    def prepare_sort_statementId(self, inst):
        if self.get_model().__name__ == "Factoid":
            if statement := inst.statement.first():
                return statement.local_id
            return SORT_LAST
        if factoid := inst.factoids.first():
            if statement := factoid.statement.first():
                return statement.local_id
            return SORT_LAST

    def prepare_sort_sourceId(self, inst):
        if self.get_model().__name__ == "Factoid":
            return inst.source.local_id
        if factoid := inst.factoids.first():
            return factoid.source.local_id
        return SORT_LAST

    def prepare_sort_factoidId(self, inst):
        if self.get_model().__name__ == "Factoid":
            return inst.local_id
        if factoid := inst.factoids.first():
            return factoid.local_id
        return SORT_LAST

    def prepare_sort_statementText(self, inst):
        if self.get_model().__name__ == "Statement":
            return inst.statementText[:20] if inst.statementText else SORT_LAST
        if self.get_model().__name__ == "Factoid":
            if statement := inst.statement.exclude(statementText="").first():
                try:
                    return statement.statementText[:20]
                except:
                    return SORT_LAST
            return SORT_LAST
        if factoid := inst.factoids.exclude(statement__statementText="").first():
            if statement := factoid.statement.exclude(statementText="").first():
                try:
                    return statement.statementText[:20]
                except:
                    return SORT_LAST
        return SORT_LAST

    def prepare_sort_relatesToPerson(self, inst):
        if self.get_model().__name__ == "Statement":
            if person := inst.relatesToPerson.first():
                return person.local_id
            return SORT_LAST
        if self.get_model().__name__ == "Factoid":
            if statement := inst.statement.first():
                if person := statement.relatesToPerson.first():
                    return person.local_id
            return SORT_LAST
        if factoid := inst.factoids.first():
            if statement := factoid.statement.first():
                if person := statement.relatesToPerson.first():
                    return person.local_id
        return SORT_LAST

    def prepare_sort_memberOf(self, inst):
        if self.get_model().__name__ == "Statement":
            return inst.memberOf_label if inst.memberOf_label else SORT_LAST
        if self.get_model().__name__ == "Factoid":
            if statement := inst.statement.exclude(memberOf_label="").first():
                return statement.memberOf_label
            return SORT_LAST
        if factoid := inst.factoids.exclude(statement__memberOf_label="").first():
            if statement := factoid.statement.exclude(memberOf_label="").first():
                return statement.memberOf_label
        return SORT_LAST

    def prepare_sort_role(self, inst):
        if self.get_model().__name__ == "Statement":
            return inst.role_label if inst.role_label else SORT_LAST
        if self.get_model().__name__ == "Factoid":
            if statement := inst.statement.exclude(role_label="").first():
                return statement.role_label
            return SORT_LAST
        if factoid := inst.factoids.exclude(statement__role_label="").first():
            if statement := factoid.statement.exclude(role_label="").first():
                return statement.role_label
        return SORT_LAST

    def prepare_sort_name(self, inst):
        if self.get_model().__name__ == "Statement":
            return inst.name if inst.name else SORT_LAST
        if self.get_model().__name__ == "Factoid":
            if statement := inst.statement.exclude(name="").first():
                return statement.name
            return SORT_LAST
        if factoid := inst.factoids.exclude(statement__name="").first():
            if statement := factoid.statement.exclude(name="").first():
                return statement.name
        return SORT_LAST

    def prepare_sort_place(self, inst):
        if self.get_model().__name__ == "Statement":
            if place := inst.places.exclude(label="").first():
                return place.label
            return SORT_LAST
        if self.get_model().__name__ == "Factoid":
            if statement := inst.statement.exclude(places__label="").first():
                if place := statement.places.first():
                    return place.label
            return SORT_LAST
        if factoid := inst.factoids.exclude(statement__places__label="").first():
            if statement := factoid.statement.exclude(places__label="").first():
                if place := statement.places.exclude(label="").first():
                    return place.label

        return SORT_LAST

    def prepare_sort_from(self, inst):
        if self.get_model().__name__ == "Statement":
            return inst.date_sortdate if inst.date_sortdate else SORT_DATE_LAST
        if self.get_model().__name__ == "Factoid":
            if (
                statement := inst.statement.exclude(date_sortdate__isnull=True)
                .order_by("date_sortdate")
                .first()
            ):
                return (
                    statement.date_sortdate
                    if statement.date_sortdate
                    else SORT_DATE_LAST
                )
            return SORT_DATE_LAST
        if (
            factoid := inst.factoids.exclude(statement__date_sortdate__isnull=True)
            .order_by("statement__date_sortdate")
            .first()
        ):
            if (
                statement := factoid.statement.exclude(date_sortdate__isnull=True)
                .order_by("date_sortdate")
                .first()
            ):
                return (
                    statement.date_sortdate
                    if statement.date_sortdate
                    else SORT_DATE_LAST
                )
        return SORT_DATE_LAST

    prepare_sort_to = prepare_sort_from

    def index_queryset(self, using=None):
        ### THIS ALSO NEEDS TO BE CHANGED TO ALSO UPDATE WHEN RELATED MODELS ARE
        ## CHANGED AS IT WILL AFFECT THE SERIALIZATION (actually, this will be done
        # automatically by saving the model, so nothing can change without being reindexed...
        # in which case, whole thing is slightly redundant???)
        """Used when the entire index for model is updated."""
        return (
            self.get_model()
            .objects.filter(hubModifiedWhen__lte=datetime.datetime.now())
            .exclude(ipif_repo__pk="IPIFHUB_AUTOCREATED")
        )


class FactoidIndex(BaseIndex, indexes.Indexable):
    st = indexes.CharField(
        use_template=True, template_name=get_template("statements_from_factoid.txt")
    )
    f = indexes.CharField(
        use_template=True, template_name=get_template("factoid_text.txt")
    )
    p = indexes.CharField(
        use_template=True, template_name=get_template("person_from_factoid.txt")
    )
    s = indexes.CharField(
        use_template=True, template_name=get_template("source_from_factoid.txt")
    )

    def get_model(self):
        return Factoid


class PersonIndex(BaseIndex, indexes.Indexable):
    uris = indexes.MultiValueField()

    st = indexes.CharField(
        use_template=True,
        template_name=get_template("statements_via_related_factoid.txt"),
    )
    f = indexes.CharField(
        use_template=True, template_name=get_template("related_factoid.txt")
    )
    s = indexes.CharField(
        use_template=True, template_name=get_template("source_via_related_factoid.txt")
    )
    p = indexes.CharField(
        use_template=True, template_name=get_template("person_text.txt")
    )

    def get_model(self):
        return Person


class SourceIndex(BaseIndex, indexes.Indexable):
    uris = indexes.MultiValueField()

    st = indexes.CharField(
        use_template=True,
        template_name=get_template("statements_via_related_factoid.txt"),
    )
    f = indexes.CharField(
        use_template=True, template_name=get_template("related_factoid.txt")
    )
    s = indexes.CharField(
        use_template=True, template_name=get_template("source_text.txt")
    )
    p = indexes.CharField(
        use_template=True, template_name=get_template("person_via_related_factoid.txt")
    )

    def get_model(self):
        return Source

    def prepare_uris(self, inst):
        values = []
        for uri in inst.uris.all():
            values.append(uri.uri)
        return values


class StatementIndex(BaseIndex, indexes.Indexable):

    st = indexes.CharField(
        use_template=True, template_name=get_template("statement_text.txt")
    )
    f = indexes.CharField(
        use_template=True, template_name=get_template("related_factoid.txt")
    )
    s = indexes.CharField(
        use_template=True, template_name=get_template("source_via_related_factoid.txt")
    )
    p = indexes.CharField(
        use_template=True, template_name=get_template("person_via_related_factoid.txt")
    )

    def get_model(self):
        return Statement


def searchQuerySet_to_querySet(sinst):
    sinst_objects = [r for r in sinst]
    if sinst_objects:
        model = sinst_objects[0].model
        return model.objects.filter(pk__in=[r.pk for r in sinst_objects])
