import datetime
import json
import os

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


class BaseIndex(indexes.SearchIndex):
    local_id = indexes.CharField(model_attr="local_id")
    ipif_repo_id = indexes.CharField()
    ipif_repo_slug = indexes.CharField()
    ipif_type = indexes.CharField()
    label = indexes.CharField(model_attr="label")
    hubModifiedWhen = indexes.DateTimeField(model_attr="hubModifiedWhen")
    pre_serialized = indexes.CharField()

    ## REMOVE default TEXT
    text = indexes.CharField(document=True, use_template=True)

    def prepare_ipif_repo_id(self, qs):
        return qs.ipif_repo.endpoint_url

    def prepare_ipif_repo_slug(self, qs):
        return qs.ipif_repo.endpoint_slug

    def prepare_ipif_type(self, qs):
        return self.get_model().__name__.lower()

    def prepare_pre_serialized(self, qs):
        serializer = globals()[f"{self.get_model().__name__}Serializer"]
        return json.dumps(serializer(qs).data)

    def prepare_uris(self, qs):
        values = []
        for uri in qs.uris.all():
            values.append(uri.uri)
        return values

    def index_queryset(self, using=None):
        ### THIS ALSO NEEDS TO BE CHANGED TO ALSO UPDATE WHEN RELATED MODELS ARE
        ## CHANGED AS IT WILL AFFECT THE SERIALIZATION (actually, this will be done
        # automatically by saving the model, so nothing can change without being reindexed...
        # in which case, whole thing is slightly redundant???)
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(
            hubModifiedWhen__lte=datetime.datetime.now()
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

    def prepare_uris(self, qs):
        values = []
        for uri in qs.uris.all():
            values.append(uri.uri)
        return values


class StatementIndex(BaseIndex, indexes.Indexable):

    # Ok, let's think through the fields we need on this.

    # st = the serialized text of this statement
    # f = the serialized metadata of the attached factoid (x1)
    # s = the serialized source of attached factoid
    # p = the serialized person of attached factoid

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


def searchQuerySet_to_querySet(sqs):
    sqs_objects = [r for r in sqs]
    if sqs_objects:
        model = sqs_objects[0].model
        return model.objects.filter(pk__in=[r.pk for r in sqs_objects])
