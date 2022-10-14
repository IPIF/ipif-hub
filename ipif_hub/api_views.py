import datetime
import json
from itertools import islice
from typing import Callable, List, Type

from dateutil.parser import parse as parse_date
from django.core.validators import URLValidator
from django.db.models import Q
from django.forms import ValidationError
from haystack.query import SQ, SearchQuerySet
from rest_framework import viewsets
from rest_framework.request import Request
from rest_framework.response import Response

from ipif_hub.models import (
    Factoid,
    IpifEntityAbstractBase,
    MergePerson,
    Person,
    Source,
    Statement,
)
from ipif_hub.search_indexes import (
    FactoidIndex,
    MergePersonIndex,
    MergeSourceIndex,
    PersonIndex,
    SourceIndex,
    StatementIndex,
)

url_validate = URLValidator()


def is_uri(s: str):
    try:
        url_validate(s)
        return True
    except ValidationError:
        return False


def build_statement_filters(request: Request) -> List[Q]:
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
            Q(relatesToPerson__uris__uri=p) | Q(relatesToPerson__identifier=p)
        )

    if p := request.query_params.get("from"):
        date = parse_date(p, default=datetime.date(1000, 1, 1))
        statement_filters.append(Q(date_sortdate__gte=date))

    if p := request.query_params.get("to"):
        date = parse_date(p, default=datetime.date(2030, 1, 1))
        statement_filters.append(Q(date_sortdate__lte=date))

    return statement_filters


def query_dict(path: str) -> Callable:
    """Creates an ORM join-path to related entities, returning
    a function that creates a dictionary

    Requests to /factoids join straight to the related models
    (no addtional path)

    Requests to /sources, /persons, /statements require join via
    `factoid__`
    """

    def inner(field, param):
        return {f"{path}{field}": param}

    return inner


from rest_framework import renderers


class AlreadyJSONRenderer(renderers.BaseRenderer):
    media_type = "application/json"
    format = "json"

    def render(self, data, media_type=None, renderer_context=None):
        return data


NOT_URI_RESPONSE = Response(
    status=400,
    data={
        "detail": (
            "Either query a specific dataset using"
            " the dataset-specific route, or provide a full URI as identifier"
        )
    },
)


def list_view(object_class: Type[IpifEntityAbstractBase]) -> Callable:
    """

    ✅ size
    ✅ page
    ✅ sortBy

    ✅ p
    ✅ factoidId
    ✅ f
    ✅ statementId
    ✅ st
    ✅ sourceId
    ✅ s"""

    # @renderer_classes([AlreadyJSONRenderer])
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

        ipif_type = object_class.__name__.lower()
        index = globals()[f"{object_class.__name__}Index"]
        if not repo and object_class.__name__ == "Person":
            index = MergePersonIndex
            ipif_type = "mergeperson"
        elif not repo and object_class.__name__ == "Source":
            index = MergeSourceIndex
            ipif_type = "mergesource"

        solr_lookup_dict = {"ipif_type": ipif_type}
        # Build lookup dict for fulltext search parameters
        for p in ["st", "s", "f", "p"]:
            if param := request_params.pop(p, None):
                solr_lookup_dict[f"{p}__contains"] = param[0]
                # For some reason ^^^^ param here is a list, this is a list...

        if not request_params:
            # If no query params apart from fulltext params (popped off above)
            # on list view, just get all the objects of a type from
            # Solr — no need to trawl through all this query stuff below
            search_queryset = (
                SearchQuerySet()
                .exclude(ipif_repo_slug="IPIFHUB_AUTOCREATED")
                .filter(**solr_lookup_dict)
            )

            if sortBy:
                search_queryset = search_queryset.order_by(sort_string)

            result = islice(
                search_queryset,
                page_start,
                page_end,
            )

            return Response([json.loads(r.pre_serialized) for r in result])

        # Otherwise, we need to create a query...

        # If it's a Person and no repo, change queryset to use
        # MergePerson, and add extra join via persons
        if not repo and object_class is Person:
            queryset = MergePerson.objects
            qd = query_dict("persons__factoids__")
        # If it's a Factoid, relations are direct, not via factoid
        elif object_class is Factoid:
            queryset = object_class.objects
            qd = query_dict("")
        # Otherwise, it's via related Factoids...
        else:
            queryset = object_class.objects
            qd = query_dict("factoids__")

        q = Q()

        if repo:
            q &= Q(ipif_repo__endpoint_slug=repo)

        if param := request.query_params.get("factoidId"):
            # If no repository is specified, the pk needs to be a URI
            if repo == None and not is_uri(param):
                return NOT_URI_RESPONSE
            q &= Q(**qd("identifier", param)) | Q(**qd("local_id", param))

        if param := request.query_params.get("statementId"):
            if repo == None and not is_uri(param):
                return NOT_URI_RESPONSE
            q &= Q(**qd("statements__identifier", param)) | Q(
                **qd("statements__local_id", param)
            )

        if param := request.query_params.get("sourceId"):
            if repo == None and not is_uri(param):
                return NOT_URI_RESPONSE
            q &= Q(**qd("source__identifier", param)) | Q(
                **qd("source__local_id", param)
            )

        if param := request.query_params.get("personId"):
            if repo == None and not is_uri(param):
                return NOT_URI_RESPONSE
            q &= Q(**qd("person__identifier", param)) | Q(
                **qd("person__local_id", param)
            )

        # Now create queryset with previously defined q object and add statement filters
        queryset = queryset.filter(q)

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
                queryset = queryset.filter(**qd("statements__in", statements))

        elif request.query_params.get("independentStatements") == "matchAny":
            st_q = Q()
            for sf in statement_filters:
                st_q |= sf
            # ...get that statement...
            statements = Statement.objects.filter(st_q)
            # ...and then apply it as a filter on the queryset
            queryset = queryset.filter(**qd("statements__in", statements))

        elif statement_filters:
            # Otherwise, build a Q object ANDing together each statement filter...
            st_q = Q()
            for sf in statement_filters:
                st_q &= sf
            # ...get that statement...
            statements = Statement.objects.filter(st_q)
            # ...and then apply it as a filter on the queryset
            queryset = queryset.filter(**qd("statements__in", statements))

        # Get serialized results from Solr, adding in any fulltext lookups
        solr_pks = [r.pk for r in queryset.distinct()]

        search_queryset = (
            SearchQuerySet()
            .exclude(ipif_repo_slug="IPIFHUB_AUTOCREATED")
            .filter(**solr_lookup_dict, django_id__in=solr_pks)
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

        # If no repository is specified, the pk needs to be a URI
        if repo == None and not is_uri(pk):
            return Response(
                status=400,
                data={
                    "detail": (
                        "Either query a specific dataset using"
                        " the dataset-specific route, or provide a full URI as identifier"
                    )
                },
            )

        ipif_type = object_class.__name__.lower()
        index = globals()[f"{object_class.__name__}Index"]
        if not repo and object_class.__name__ == "Person":
            index = MergePersonIndex
            ipif_type = "mergeperson"
        elif not repo and object_class.__name__ == "Source":
            index = MergeSourceIndex
            ipif_type = "mergesource"

        sq = SQ(ipif_type=ipif_type) & (
            SQ(identifier=pk) | SQ(uris=pk) | (SQ(local_id=pk))
        )

        if repo:
            sq &= SQ(ipif_repo_slug=repo)
        result = index.objects.filter(sq).values("pre_serialized")
        try:
            return Response(json.loads(result[0]["pre_serialized"]))
        except IndexError:
            return Response(status=404)

    return inner


def build_viewset(object_class: Type[IpifEntityAbstractBase]) -> Type[viewsets.ViewSet]:
    viewset_name = f"{object_class.__name__}ViewSet"

    vs: Type[viewsets.ViewSet] = type(
        viewset_name,
        (viewsets.ViewSet,),
        {
            # "pagination_class": StandardResultsSetPagination, # does not work
            "list": list_view(object_class),
            "retrieve": retrieve_view(object_class),
        },
    )
    return vs


# Construct these viewsets
PersonViewSet = build_viewset(Person)
SourceViewSet = build_viewset(Source)
FactoidViewSet = build_viewset(Factoid)
StatementViewSet = build_viewset(Statement)
