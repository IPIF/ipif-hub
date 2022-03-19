import datetime
import json

from haystack import indexes

from .models import Person, Source


class PersonIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)
    label = indexes.CharField(model_attr="label")
    hubModifiedWhen = indexes.DateTimeField(model_attr="hubModifiedWhen")
    pre_serialized = indexes.CharField()
    uris = indexes.MultiValueField()

    def prepare_pre_serialized(self, qs):
        return json.dumps(qs.pre_serialized)

    def prepare_uris(self, qs):
        print(">>>>", qs.uris.all())
        values = []
        for uri in qs.uris.all():
            values.append(uri.uri)
        print(values)
        return values

    def get_model(self):
        return Person

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.filter(
            hubModifiedWhen__lte=datetime.datetime.now()
        )


def searchQuerySet_to_querySet(sqs):
    sqs_objects = [r for r in sqs]
    if sqs_objects:
        model = sqs_objects[0].model
        return model.objects.filter(pk__in=[r.pk for r in sqs_objects])
