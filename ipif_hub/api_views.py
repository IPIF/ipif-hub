from dataclasses import field
from itertools import islice
import json
from typing import List

from django.db.models import Q

from rest_framework import viewsets
from rest_framework.response import Response

from haystack.query import SQ, SearchQuerySet
from haystack.inputs import Raw

import datetime
from dateutil.parser import parse as parse_date

from .models import Factoid, Person, Source, Statement
from .search_indexes import PersonIndex, FactoidIndex, SourceIndex, StatementIndex
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


def list_view(object_class):
    """

    ✅ size
    ✅ page
    sortBy

    ✅ p
    ✅ factoidId
    ✅ f
    ✅ statementId
    ✅ st
    ✅ sourceId
    ✅ s"""

    def inner(self, request, repo=None):

        # Make a copy of this so we can pop off the fulltext fields and
        # check whether there are any fields afterwards
        request_params = request.query_params.copy()

        # Get the size and page params, to pass to islice (hopefully this works?)
        size = 30
        if s := request_params.pop("size", None):
            size = int(s[0])
        page_start = 0

        if p := request_params.pop("page", None):
            page_start = (int(p[0]) - 1) * size
        page_end = page_start + size

        sortBy = ""
        sort_order = ""
        if s := request_params.pop("sortBy", ""):
            sortBy = s[0]

        if sortBy.endswith("ASC"):
            sortBy = sortBy.replace("ASC", "").strip()

        if sortBy.endswith("DESC"):
            sortBy = sortBy.replace("DESC", "").strip()
            sort_order = "-"

        if sortBy in {"p", "s", "st", "s"}:
            # These fields already exist in index so we don't need the 'sort_' prefix
            sort_string = f"{sort_order}{sortBy}"
        else:
            sort_string = f"{sort_order}sort_{sortBy}"

        # Build lookup dict for fulltext search parameters
        fulltext_lookup_dict = {"ipif_type": object_class.__name__.lower()}
        for p in ["st", "s", "f", "p"]:
            if param := request_params.pop(p, None):
                fulltext_lookup_dict[f"{p}__contains"] = param[0]
                # For some reason ^^^^ param here is a list, this is a list...

        if not request_params:
            # If no query params apart from fulltext params (popped off above)
            # on list view, just get all the objects of a type from
            # Solr — no need to trawl through all this query stuff below
            search_queryset = (
                SearchQuerySet()
                .exclude(ipif_repo_slug="IPIFHUB_AUTOCREATED")
                .filter(**fulltext_lookup_dict)
            )

            if sortBy:
                search_queryset = search_queryset.order_by(sort_string)
            result = islice(search_queryset, page_start, page_end)

            return Response([json.loads(r.pre_serialized) for r in result])

        # Otherwise, we need to create a query...

        # Fields are directly on Factoids, unlike other models where we
        # need to access *via* a Factoid
        if object_class is Factoid:
            qd = query_dict("")
        else:
            qd = query_dict("factoids__")

        q = Q()

        if repo:
            q &= Q(ipif_repo__endpoint_slug=repo)

        if param := request.query_params.get("factoidId"):
            q &= Q(**qd("id", param))

        if param := request.query_params.get("statementId"):
            q &= Q(**qd("statement__id", param))

        if param := request.query_params.get("sourceId"):
            q &= Q(**qd("source__id", param))

        # Now create queryset with previously defined q object and add statement filters
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

        elif statement_filters:
            # Otherwise, build a Q object ANDing together each statement filter...
            st_q = Q()
            for sf in statement_filters:
                st_q &= sf
            # ...get that statement...
            statements = Statement.objects.filter(st_q)
            # ...and then apply it as a filter on the queryset
            queryset = queryset.filter(**qd("statement__in", statements))

        # Get serialized results from Solr, adding in any fulltext lookups
        solr_pks = [r.pk for r in queryset.distinct()]

        search_queryset = (
            SearchQuerySet()
            .exclude(ipif_repo_slug="IPIFHUB_AUTOCREATED")
            .filter(**fulltext_lookup_dict, django_id__in=solr_pks)
        )

        if sortBy:
            search_queryset = search_queryset.order_by(sort_string)

        result = islice(
            search_queryset,
            page_start,
            page_end,
        )

        return Response([json.loads(r.pre_serialized) for r in result])

    return inner


def retrieve_view(object_class):

    # OLD VERSION HITTING DB
    """
    def inner(self, request, pk=None):
        q = Q(pk=pk)
        if object_class in {Person, Source}:  # Only Person and Source have `uris` field
            q |= Q(uris__uri=pk)
        queryset = object_class.objects.filter(q).first()
        serializer = globals()[f"{object_class.__name__}Serializer"]
        return Response(serializer(queryset).data)
    """
    # New version hitting SOLR

    def inner(self, request, pk, repo=None):
        index = globals()[f"{object_class.__name__}Index"]
        sq = (
            SQ(id=f"ipif_hub.{object_class.__name__.lower()}.{pk}")
            | SQ(uris=pk)
            | (SQ(local_id=pk) & SQ(ipif_type=object_class.__name__.lower()))
        )

        if repo:
            sq &= SQ(ipif_repo_slug=repo)
        result = index.objects.filter(sq)
        try:
            return Response(json.loads(result[0].pre_serialized))
        except IndexError:
            return Response(status=404)

    return inner


from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 1
    page_size_query_param = "page_size"
    max_page_size = 1000


def build_viewset(object_class) -> viewsets.ViewSet:
    viewset = f"{object_class.__name__}ViewSet"
    # serializer = globals()[f"{object_class.__name__}Serializer"]
    return type(
        viewset,
        (viewsets.ViewSet,),
        {
            "pagination_class": StandardResultsSetPagination,
            "list": list_view(object_class),
            "retrieve": retrieve_view(object_class),
        },
    )


# Construct these viewsets
PersonViewSet = build_viewset(Person)
SourceViewSet = build_viewset(Source)
FactoidViewSet = build_viewset(Factoid)
StatementViewSet = build_viewset(Statement)
