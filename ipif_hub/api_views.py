from django.db.models import Q

from rest_framework import viewsets
from rest_framework.response import Response


from .models import Factoid, Person, Source, Statement
from .serializers import (
    FactoidSerializer,
    PersonSerializer,
    SourceSerializer,
    StatementSerializer,
)


class PersonsViewSet(viewsets.ViewSet):
    def list(self, request):
        queryset = Person.objects.all()
        serializer = PersonSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Person.objects.filter(Q(pk=pk) | Q(uris__uri=pk)).first()
        print(queryset)
        serializer = PersonSerializer(queryset)
        return Response(serializer.data)


class SourceViewSet(viewsets.ViewSet):
    def list(self, request):
        queryset = Source.objects.all()
        serializer = SourceSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Source.objects.filter(Q(pk=pk) | Q(uris__uri=pk)).first()
        serializer = SourceSerializer(queryset)
        return Response(serializer.data)


class FactoidViewSet(viewsets.ViewSet):
    def list(self, request):
        queryset = Factoid.objects.all()
        serializer = FactoidSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Factoid.objects.filter(pk=pk).first()
        serializer = FactoidSerializer(queryset)
        return Response(serializer.data)


class StatementViewSet(viewsets.ViewSet):
    def list(self, request):
        queryset = Statement.objects.all()
        serializer = StatementSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Statement.objects.filter(pk=pk).first()
        serializer = StatementSerializer(queryset)
        return Response(serializer.data)
