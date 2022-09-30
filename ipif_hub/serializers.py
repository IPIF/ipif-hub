from itertools import filterfalse

from django.conf import settings
from rest_framework import serializers

from ipif_hub.models import (
    URI,
    Factoid,
    MergePerson,
    MergeSource,
    Person,
    Place,
    Source,
    Statement,
)


class URISerlializer(serializers.ModelSerializer):
    class Meta:
        model = URI
        fields = ["uri"]


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ["uri", "label"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {"label": data["label"], "uri": data["uri"]}


class GenericRefSerializer:
    def to_representation(self, instance):
        data = super().to_representation(instance)
        id = data.pop("identifier", "")

        return {"@id": id, **data}


class PersonRefSerializer(GenericRefSerializer, serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ["identifier", "label"]


class SourceRefSerializer(GenericRefSerializer, serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ["identifier", "label"]


class StatementRefSerializer(GenericRefSerializer, serializers.ModelSerializer):
    class Meta:
        model = Statement
        fields = ["identifier", "label"]


class FactoidRefSerializer(GenericRefSerializer, serializers.ModelSerializer):

    person = PersonRefSerializer()
    source = SourceRefSerializer()
    statements = StatementRefSerializer(many=True)

    class Meta:
        model = Factoid
        fields = ["identifier", "label", "person", "source", "statements"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        person = data.pop("person")
        source = data.pop("source")
        statements = data.pop("statements")
        return {
            **data,
            "person-ref": person,
            "source-ref": source,
            "statement-refs": statements,
        }


class FactoidSerializer(FactoidRefSerializer):
    class Meta:
        model = Factoid
        fields = [
            "identifier",
            "id",
            "label",
            "person",
            "source",
            "statements",
            "createdBy",
            "createdWhen",
            "modifiedBy",
            "modifiedWhen",
        ]


class PersonSerializer(serializers.ModelSerializer):
    uris = URISerlializer(many=True)
    factoids = FactoidRefSerializer(many=True)

    class Meta:
        model = Person
        fields = [
            "identifier",
            "id",
            "label",
            "uris",
            "factoids",
            "createdBy",
            "createdWhen",
            "modifiedBy",
            "modifiedWhen",
        ]
        depth = 1

    def to_representation(self, instance):
        data = super().to_representation(instance)
        id = data.pop("identifier", "no")

        label = data.pop("label", "")
        factoids = data.pop("factoids")
        uris = [v["uri"] for v in data.pop("uris")]

        return_data = {
            "@id": id,
            "label": label,
            "uris": uris,
            **data,
            "factoid-refs": factoids,
        }

        return return_data


class SourceSerializer(serializers.ModelSerializer):
    uris = URISerlializer(many=True)
    factoids = FactoidRefSerializer(many=True)

    class Meta:
        model = Source
        fields = [
            "identifier",
            "id",
            "label",
            "uris",
            "factoids",
            "createdBy",
            "createdWhen",
            "modifiedBy",
            "modifiedWhen",
        ]
        depth = 1

    def to_representation(self, instance):
        data = super().to_representation(instance)
        identifier = data.pop("identifier", "")
        label = data.pop("label", "")
        factoids = data.pop("factoids")

        uris = [v["uri"] for v in data.pop("uris")]
        return {
            "@id": identifier,
            "label": label,
            "uris": uris,
            **data,
            "factoid-refs": factoids,
        }


class StatementSerializer(GenericRefSerializer, serializers.ModelSerializer):
    places = PlaceSerializer(many=True)
    factoids = FactoidRefSerializer(many=True)

    class Meta:
        depth = 2
        model = Statement
        exclude = [
            "local_id",
            "inputContentHash",
            "ipif_repo",
            "hubIngestedWhen",
            "hubModifiedWhen",
            "id",
        ]

    def to_representation(self, instance):
        """Converts Statement data to IPIF output format:

        Fields containing an underscore should be split on underscore and
        made into nested dicts
        """
        data = super().to_representation(instance)

        return_dict = {}
        for k, v in data.items():

            if "_" in k:
                field, subfield = k.split("_")
                if field in return_dict:
                    return_dict[field][subfield] = v
                else:
                    return_dict[field] = {subfield: v}
            elif k == "relatesToPerson":
                return_dict[k] = [
                    {"uri": p["identifier"], "label": p["label"]} for p in v
                ]
            else:
                return_dict[k] = v
        return_dict["factoid-refs"] = return_dict.pop("factoids")

        return return_dict


from functools import cache


class MergePersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = MergePerson
        exclude = ["persons"]

    def to_representation(self, instance: MergePerson):

        data = super().to_representation(instance)
        _ = data.pop("id")
        uris = list(instance.uri_set)
        chosen_uri = "http://merge_source.com"

        for uri in uris:
            if not uri.startswith(settings.IPIF_BASE_URI):
                chosen_uri = uri
                break

        return_data = {"@id": chosen_uri, **data}
        return_data["uris"] = uris

        return_data["factoid-refs"] = []

        for person in instance.persons.all():
            if factoids := person.factoids.all():
                return_data["factoid-refs"] += FactoidRefSerializer(
                    factoids, many=True
                ).data

        return return_data


class MergeSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MergeSource
        exclude = ["sources"]

    def to_representation(self, instance: MergeSource):

        data = super().to_representation(instance)
        _ = data.pop("id")
        uris = list(instance.uri_set)
        chosen_uri = "http://merge_source.com"
        for uri in uris:
            if not uri.startswith(settings.IPIF_BASE_URI):
                chosen_uri = uri
                break

        return_data = {"@id": chosen_uri, **data}
        return_data["uris"] = uris

        return_data["factoid-refs"] = []

        for source in instance.sources.all():
            if factoids := source.factoids.all():
                return_data["factoid-refs"] += FactoidRefSerializer(
                    factoids, many=True
                ).data

        return return_data
