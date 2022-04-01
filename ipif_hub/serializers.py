import re
from rest_framework import serializers

from .models import Person, URI, Factoid, Place, Source, Statement


class URISerlializer(serializers.ModelSerializer):
    class Meta:
        model = URI
        fields = ["uri"]


class GenericRefSerializer:
    def to_representation(self, instance):
        data = super().to_representation(instance)
        id = data.pop("id", "")
        return {"@id": id, **data}


class PlacesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ["uri", "label"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {"@id": data["uri"], "label": data["label"], "uri": data["uri"]}


class PersonRefSerializer(GenericRefSerializer, serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ["id", "label"]


class SourceRefSerializer(GenericRefSerializer, serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ["id", "label"]


class StatementRefSerializer(GenericRefSerializer, serializers.ModelSerializer):
    class Meta:
        model = Statement
        fields = ["id"]


class FactoidRefSerializer(GenericRefSerializer, serializers.ModelSerializer):

    person = PersonRefSerializer()
    source = SourceRefSerializer()
    statement = StatementRefSerializer(many=True)

    class Meta:
        model = Factoid
        fields = ["id", "person", "source", "statement"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        person = data.pop("person")
        source = data.pop("source")
        statements = data.pop("statement")
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
            "id",
            "person",
            "source",
            "statement",
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
        id = data.pop("id", "")
        label = data.pop("label", "")
        factoids = data.pop("factoids")
        uris = [v["uri"] for v in data.pop("uris")]
        return {
            "@id": id,
            "label": label,
            "uris": uris,
            **data,
            "factoid-refs": factoids,
        }


class SourceSerializer(serializers.ModelSerializer):
    uris = URISerlializer(many=True)
    factoids = FactoidRefSerializer(many=True)

    class Meta:
        model = Source
        fields = [
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
        id = data.pop("id", "")
        label = data.pop("label", "")
        factoids = data.pop("factoids")
        uris = [v["uri"] for v in data.pop("uris")]
        return {
            "@id": id,
            "label": label,
            "uris": uris,
            **data,
            "factoid-refs": factoids,
        }


class StatementSerializer(GenericRefSerializer, serializers.ModelSerializer):
    places = PlacesSerializer(many=True)
    factoids = FactoidSerializer(many=True)

    class Meta:
        model = Statement
        exclude = [
            "ipif_repo",
            "hubIngestedWhen",
            "hubModifiedWhen",
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
            else:
                return_dict[k] = v
        return_dict["factoid-refs"] = return_dict.pop("factoids")
        return return_dict
