from django.db.models import Q

from rest_framework import viewsets
from rest_framework.response import Response

import datetime
from dateutil.parser import parse as parse_date


from .models import Factoid, Person, Source, Statement
from .serializers import (
    FactoidSerializer,
    PersonSerializer,
    SourceSerializer,
    StatementSerializer,
)


def apply_statement_filters(q: Q, object_class, request) -> Q:
    """
    ✅ statementText
    ✅ relatesToPerson
    ✅ memberOf
    ✅ role
    ✅ name
    ✅ from
    ✅ to
    ✅ place
    """

    # Make a list of Q objects, which can be combined with AND/OR later
    # depending on `independentStatements` flag
    statement_filters = []

    if p := request.query_params.get("statementText"):
        statement_filters.append(Q(statementText__contains=p))

    if p := request.query_params.get("name"):
        statement_filters.append(Q(name=p))

    if p := request.query_params.get("role"):
        statement_filters.append(Q(role_uri=p) | Q(role_label=p))

    if p := request.query_params.get("memberOf"):
        statement_filters.append(Q(memberOf_uri=p) | Q(memberOf_label=p))

    if p := request.query_params.get("place"):
        statement_filters.append(Q(places__uri=p) | Q(places__label=p))

    if p := request.query_params.get("relatesToPerson"):
        statement_filters.append(
            Q(relatesToPerson__uris__uri=p) | Q(relatesToPerson__id=p)
        )

    if p := request.query_params.get("from"):
        date = parse_date(p, default=datetime.date(1000, 1, 1))
        statement_filters.append(Q(date_sortdate__gte=date))

    if p := request.query_params.get("to"):
        date = parse_date(p, default=datetime.date(2030, 1, 1))
        statement_filters.append(Q(date_sortdate__lte=date))

    # If no statement filters are found, just return the Q object early
    if not statement_filters:
        return q

    # Create a statement Q object
    st_q = Q()

    # If independentStatements flag set, each statement filter can belong to any statem
    if request.query_params.get("independentStatements") == "true":

        statements = Statement.objects.all(sf)
        for sf in statement_filters:
            s = Statement.objects.filter(sf)
            if s:
                statements.append(s)
            else:
                print("NO SUCH LUCK")
                return "NO SUCH LUCK"

    else:
        for sf in statement_filters:
            st_q &= sf
        statements = Statement.objects.filter(st_q)
        q &= Q(factoids__statement__in=statements)

    return q


class PersonsViewSet(viewsets.ViewSet):
    def list(self, request):

        q = Q()

        if p := request.query_params.get("factoidId"):
            q &= Q(factoids__id=p)

        if p := request.query_params.get("statementId"):
            q &= Q(factoids__statement__id=p)

        if p := request.query_params.get("sourceId"):
            q &= Q(factoids__source__id=p)

        q = apply_statement_filters(q, Person, request)

        queryset = Person.objects.filter(q).distinct()

        serializer = PersonSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Person.objects.filter(Q(pk=pk) | Q(uris__uri=pk)).first()
        print(queryset)
        serializer = PersonSerializer(queryset)
        return Response(serializer.data)


"""
size
page
sortBy

p
✅ factoidId
f
✅ statementId
st
✅ sourceId
s


"""


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
