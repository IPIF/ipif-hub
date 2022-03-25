import json
from typing import List


from django.db.models import Q

from rest_framework import viewsets
from rest_framework.response import Response

import datetime
from dateutil.parser import parse as parse_date


from .models import Factoid, Person, Source, Statement
from .search_indexes import PersonIndex
from .serializers import (
    FactoidSerializer,
    PersonSerializer,
    SourceSerializer,
    StatementSerializer,
)


def build_statement_filters(request) -> List:
    """
    Builds a list of statement filters

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

    return statement_filters


def query_dict(path):
    def inner(field, param):
        return {f"{path}{field}": param}

    return inner


def list_view(object_class, serializer_class):
    """

    p
    ✅ factoidId
    f
    ✅ statementId
    st
    ✅ sourceId
    s"""

    def inner(self, request):

        # Fields are directly on Factoids, unlike other models where we
        # need to access *via* a Factoid
        if object_class is Factoid:
            qd = query_dict("")
        else:
            qd = query_dict("factoids__")

        q = Q()

        if p := request.query_params.get("factoidId"):
            q &= Q(**qd("id", p))

        if p := request.query_params.get("statementId"):
            q &= Q(**qd("statement__id", p))

        if p := request.query_params.get("sourceId"):
            q &= Q(**qd("source__id", p))

        queryset = object_class.objects.filter(q)

        statement_filters = build_statement_filters(request)

        # If querying /statements endpoint, statement_filters should be applied
        # directly to the statement queryset
        if object_class == Statement:
            st_q = Q()
            for sf in statement_filters:
                st_q &= sf
            queryset = queryset.filter(st_q)

        elif request.query_params.get("independentStatements") == "matchAll":
            # Go through each statement filter
            for sf in statement_filters:
                # Get the statements that correspond to that filter
                statements = Statement.objects.filter(sf)
                # Apply as a filter to queryset
                queryset = queryset.filter(**qd("statement__in", statements))

        elif request.query_params.get("independentStatements") == "matchAny":
            st_q = Q()
            for sf in statement_filters:
                st_q |= sf
            # ...get that statement...
            statements = Statement.objects.filter(st_q)
            # ...and then apply it as a filter on the queryset
            queryset = queryset.filter(**qd("statement__in", statements))

        else:
            # Otherwise, build a Q object ANDing together each statement filter...
            st_q = Q()
            for sf in statement_filters:
                st_q &= sf
            # ...get that statement...
            statements = Statement.objects.filter(st_q)
            # ...and then apply it as a filter on the queryset
            queryset = queryset.filter(**qd("statement__in", statements))

        # Finally, get the pre-serialized result from the db and return
        queryset = queryset.distinct().values("pre_serialized")
        result = [o["pre_serialized"] for o in queryset]
        return Response(result)

    return inner


def retrieve_view(object_class, object_serializer):

    # OLD VERSION HITTING DB
    """
    def inner(self, request, pk=None):
        q = Q(pk=pk)
        if object_class in {Person, Source}:  # Only Person and Source have `uris` field
            q |= Q(uris__uri=pk)
        queryset = object_class.objects.filter(q).first()
        serializer = globals()[f"{object_class.__name__}Serializer"]
        return Response(serializer(queryset).data)

    # New version hitting SOLR
    """

    def inner(self, request, pk):
        print("getting")
        index = globals()[f"{object_class.__name__}Index"]
        result = index.objects.filter(
            id=f"ipif_hub.{object_class.__name__.lower()}.{pk}"
        )
        try:
            return Response(json.loads(result[0].pre_serialized))
        except IndexError:
            return Response(status=404)

    # """

    return inner


def build_viewset(object_class) -> viewsets.ViewSet:
    viewset = f"{object_class.__name__}ViewSet"
    serializer = globals()[f"{object_class.__name__}Serializer"]
    return type(
        viewset,
        (viewsets.ViewSet,),
        {
            "list": list_view(object_class, serializer),
            "retrieve": retrieve_view(object_class, serializer),
        },
    )


# Construct these viewsets
PersonViewSet = build_viewset(Person)
SourceViewSet = build_viewset(Source)
FactoidViewSet = build_viewset(Factoid)
StatementViewSet = build_viewset(Statement)
