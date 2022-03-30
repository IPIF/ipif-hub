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


class PersonIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)
    ipif_repo_id = indexes.CharField()

    label = indexes.CharField(model_attr="label")
    hubModifiedWhen = indexes.DateTimeField(model_attr="hubModifiedWhen")
    pre_serialized = indexes.CharField()
    uris = indexes.MultiValueField()

    def prepare_ipif_repo_id(self, qs):
        return qs.ipif_repo.id

    def prepare_pre_serialized(self, qs):
        return json.dumps(PersonSerializer(qs).data)

    def prepare_uris(self, qs):
        values = []
        for uri in qs.uris.all():
            values.append(uri.uri)
        print(values)
        return values

    def get_model(self):
        return Person

    def index_queryset(self, using=None):
        ### THIS ALSO NEEDS TO BE CHANGED TO ALSO UPDATE WHEN RELATED MODELS ARE
        ## CHANGED AS IT WILL AFFECT THE SERIALIZATION (actually, this will be done
        # automatically by saving the model, so nothing can change without being reindexed...
        # in which case, whole thing is slightly redundant???)
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(
            hubModifiedWhen__lte=datetime.datetime.now()
        )


class FactoidIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)
    ipif_repo_id = indexes.CharField()
    hubModifiedWhen = indexes.DateTimeField(model_attr="hubModifiedWhen")
    pre_serialized = indexes.CharField()

    def prepare_ipif_repo_id(self, qs):
        return qs.ipif_repo.id

    def prepare_pre_serialized(self, qs):
        return json.dumps(FactoidSerializer(qs).data)

    def get_model(self):
        return Factoid

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(
            hubModifiedWhen__lte=datetime.datetime.now()
        )


class SourceIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)
    ipif_repo_id = indexes.CharField()
    hubModifiedWhen = indexes.DateTimeField(model_attr="hubModifiedWhen")
    pre_serialized = indexes.CharField()
    uris = indexes.MultiValueField()

    def prepare_ipif_repo_id(self, qs):
        return qs.ipif_repo.id

    def prepare_pre_serialized(self, qs):
        return json.dumps(SourceSerializer(qs).data)

    def get_model(self):
        return Source

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(
            hubModifiedWhen__lte=datetime.datetime.now()
        )


class StatementIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    ipif_repo_id = indexes.CharField()

    hubModifiedWhen = indexes.DateTimeField(model_attr="hubModifiedWhen")
    pre_serialized = indexes.CharField()

    def prepare_pre_serialized(self, qs):
        return json.dumps(StatementSerializer(qs).data)

    def prepare_ipif_repo_id(self, qs):
        return qs.ipif_repo.id

    def get_model(self):
        return Statement


def searchQuerySet_to_querySet(sqs):
    sqs_objects = [r for r in sqs]
    if sqs_objects:
        model = sqs_objects[0].model
        return model.objects.filter(pk__in=[r.pk for r in sqs_objects])
