import datetime
import json

from haystack import indexes

from ipif_hub.serializers import (
    FactoidSerializer,
    PersonSerializer,
    SourceSerializer,
    StatementSerializer,
)

from .models import Person, Source, Factoid, Statement


class BaseIndex(indexes.SearchIndex):
    local_id = indexes.CharField(model_attr="local_id")
    ipif_repo_id = indexes.CharField()
    ipif_type = indexes.CharField()
    label = indexes.CharField(model_attr="label")
    hubModifiedWhen = indexes.DateTimeField(model_attr="hubModifiedWhen")
    pre_serialized = indexes.CharField()
    text = indexes.CharField(document=True, use_template=True)

    def prepare_ipif_repo_id(self, qs):
        return qs.ipif_repo.endpoint_url

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
    def get_model(self):
        return Factoid


class PersonIndex(BaseIndex, indexes.Indexable):
    uris = indexes.MultiValueField()

    def get_model(self):
        return Person


class SourceIndex(BaseIndex, indexes.Indexable):
    uris = indexes.MultiValueField()

    def get_model(self):
        return Source


class StatementIndex(BaseIndex, indexes.Indexable):
    def get_model(self):
        return Statement


def searchQuerySet_to_querySet(sqs):
    sqs_objects = [r for r in sqs]
    if sqs_objects:
        model = sqs_objects[0].model
        return model.objects.filter(pk__in=[r.pk for r in sqs_objects])
