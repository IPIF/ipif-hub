import datetime
import json
from itertools import islice
from typing import Callable, List, Type

from dateutil.parser import parse as parse_date
from django.conf import settings
from django.core.validators import URLValidator
from django.db.models import Q
from django.forms import ValidationError
from django.views.decorators.csrf import csrf_exempt
from haystack.query import SQ, SearchQuerySet
from jsonschema import ValidationError as JSONValidationError
from jsonschema import validate
from rest_framework import viewsets
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.response import Response

from ipif_hub.management.utils.ingest_data import (
    DataFormatError,
    ingest_factoids,
    ingest_persons,
    ingest_sources,
    ingest_statements,
)
from ipif_hub.management.utils.ingest_schemas import (
    FACTOID_LIST,
    PERSON_SOURCE_LIST,
    STATEMENT_LIST,
)
from ipif_hub.models import (
    Factoid,
    IpifEntityAbstractBase,
    IpifRepo,
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


def get_index_from_model(index):
    return {
        Person: PersonIndex,
        Factoid: FactoidIndex,
        Source: SourceIndex,
        Statement: StatementIndex,
    }[index]


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
        if p == "*":
            statement_filters.append(
                (Q(statementText__isnull=False) & ~Q(statementText__exact=""))
            )
        else:
            statement_filters.append(Q(statementText__contains=p))

    if p := request.query_params.get("name"):
        if p == "*":
            statement_filters.append(Q(name__isnull=False) & ~Q(name__exact=""))
        else:
            statement_filters.append(Q(name=p))

    if p := request.query_params.get("role"):
        if p == "*":
            statement_filters.append(
                (Q(role_uri__isnull=False) & ~Q(role_uri__exact=""))
                | (Q(role_label__isnull=False) & ~Q(role_label__exact=""))
            )
        else:
            statement_filters.append(Q(role_uri=p) | Q(role_label=p))

    if p := request.query_params.get("memberOf"):
        if p == "*":
            statement_filters.append(
                (Q(memberOf_uri__isnull=False) & ~Q(memberOf_uri__exact=""))
                | (Q(memberOf_label__isnull=False) & ~Q(memberOf_label__exact=""))
            )
        else:
            statement_filters.append(Q(memberOf_uri=p) | Q(memberOf_label=p))

    if p := request.query_params.get("place"):
        if p == "*":
            statement_filters.append(
                (Q(places__uri__isnull=False) & ~Q(places__uri__exact=""))
                | (Q(places__label__isnull=False) & ~Q(places__label__exact=""))
            )
        else:
            statement_filters.append(Q(places__uri=p) | Q(places__label=p))

    if p := request.query_params.get("relatesToPerson"):
        if p == "*":
            statement_filters.append(
                (
                    Q(relatesToPerson__uris__uri__isnull=False)
                    & ~Q(relatesToPerson__uris__uri__exact="")
                )
                | (
                    Q(relatesToPerson__identifier__isnull=False)
                    & ~Q(relatesToPerson__identifier__exact="")
                )
            )
        else:
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

    def inner(self, request, repo=None):

        # Make a copy of this so we can pop off the fulltext fields and
        # check whether there are any fields afterwards
        request_params = request.query_params.copy()

        # Get the size and page params, to pass to islice (hopefully this works?)
        size = 30
        if s := request_params.pop("size", None):
            size = int(s[0])
        page_start = 0

        # Get the page number
        if p := request_params.pop("page", None):
            page_start = (int(p[0]) - 1) * size
        page_end = page_start + size

        # Build sortBy and sort_order param by stripping "ASC"/"DESC"
        sortBy = ""
        sort_order = ""
        if s := request_params.pop("sortBy", ""):
            sortBy = s[0]

        if sortBy.endswith("ASC"):
            sortBy = sortBy.replace("ASC", "").strip()

        if sortBy.endswith("DESC"):
            sortBy = sortBy.replace("DESC", "").strip()
            sort_order = "-"

        # Assemble a sort_string with above options
        if sortBy in {"p", "s", "st", "s"}:
            # These fields already exist in index so we don't need the 'sort_' prefix
            sort_string = f"{sort_order}{sortBy}"
        else:
            # otherwise, use the solr 'sort_X' fields
            sort_string = f"{sort_order}sort_{sortBy}"

        # Set the correct ipif_type string -- should use MergeX if no repo specified
        ipif_type = object_class.__name__.lower()
        if not repo and object_class.__name__ == "Person":
            ipif_type = "mergeperson"
        elif not repo and object_class.__name__ == "Source":
            ipif_type = "mergesource"

        # Start constructing the solr lookup as dict to be expanded into filter
        solr_lookup_dict = {"ipif_type": ipif_type}
        # Build lookup dict for fulltext search parameters
        for p in ["st", "s", "f", "p"]:
            if param := request_params.pop(p, None):
                solr_lookup_dict[f"{p}__contains"] = param[0]
                # For some reason ^^^^ param here is a list, this is a list...

        # If no query params apart from fulltext params remain (popped off above)
        # on list view, just get all the objects of a type from
        # Solr — no need to trawl through all this query stuff below
        if not request_params:

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

        # Otherwise, we need to create a query using the Django ORM...

        # Start by setting the correct queryset, and the qd function
        # which prefixes later query params with the correct path

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

        # Start by constructing the Q object for ORM query
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

        # Now create queryset with previously defined q object
        queryset = queryset.filter(q)

        # ... and add statement filters
        statement_filters = build_statement_filters(request)

        # If querying /statements endpoint directly, statement_filters should be applied
        # directly to the statement queryset [only need to match the one statement]
        if object_class == Statement:
            st_q = Q()
            for sf in statement_filters:
                st_q &= sf
            queryset = queryset.filter(st_q)

        # in case of "matchAll", all the supplied filters must apply, but not
        # necessarily to the same statement
        elif request.query_params.get("independentStatements") == "matchAll":
            # Go through each statement filter
            for sf in statement_filters:
                # Get the statements that correspond to that filter
                statements = Statement.objects.filter(sf)
                # Apply as a filter to queryset
                queryset = queryset.filter(**qd("statements__in", statements))

        # in case of "matchAny", any one of the supplied filters needs to apply,
        # to any related statement
        elif request.query_params.get("independentStatements") == "matchAny":
            st_q = Q()
            for sf in statement_filters:
                st_q |= sf
            # ...get that statement...
            statements = Statement.objects.filter(st_q)
            # ...and then apply it as a filter on the queryset
            queryset = queryset.filter(**qd("statements__in", statements))

        # if no independentStatment flag, all the supplied filters must
        # relate to the same statement
        elif statement_filters:
            # Otherwise, build a Q object ANDing together each statement filter...
            st_q = Q()
            for sf in statement_filters:
                st_q &= sf
            # ...get that statement...
            statements = Statement.objects.filter(st_q)
            # ...and then apply it as a filter on the queryset
            queryset = queryset.filter(**qd("statements__in", statements))

        # Get all the pks from Django ORM
        pks_for_solr_lookup = [r.id for r in queryset.distinct().only("id")]

        # Create the solr queryset... apply the previously-created solr lookup dict
        # and the filtered pks from the ORM query
        search_queryset = (
            SearchQuerySet()
            .exclude(ipif_repo_slug="IPIFHUB_AUTOCREATED")
            .filter(**solr_lookup_dict, django_id__in=pks_for_solr_lookup)
        )
        # Add in sortBy params if any
        if sortBy:
            search_queryset = search_queryset.order_by(sort_string)

        # Get the sliced result using page_start,end
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
        index = get_index_from_model(object_class)
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


def post_view(object_class):
    @action(
        detail=True,
        methods=["post"],
        authentication_classes=[BasicAuthentication],
    )
    def inner(self, request, repo=None):
        if repo == None:
            return Response(
                status=400,
                data={
                    "detail": (
                        "Updates must be made to a specific repository. "
                        f"i.e. {settings.IPIF_BASE_URI}/[repository-name]/ipif/{object_class.__name__.lower()}s/"
                    )
                },
            )
        ipif_repo = IpifRepo.objects.get(pk=repo)
        if not ipif_repo:
            return Response(
                status=404,
                data={"detail": (f"Repository '{repo}' does not exist.")},
            )

        if object_class is Person:
            try:
                validate(request.data, PERSON_SOURCE_LIST)
            except JSONValidationError as e:
                return Response({"detail": e.message}, status=400)
            try:
                resp = ingest_persons(request.data, ipif_repo=ipif_repo)
            except DataFormatError as e:
                return Response({"detail": e.message}, status=400)
            return Response({"detail": resp})

        elif object_class is Factoid:
            try:
                validate(request.data, FACTOID_LIST)
            except JSONValidationError as e:
                return Response({"detail": e.message}, status=400)
            try:
                resp = ingest_factoids(request.data, ipif_repo=ipif_repo)
            except DataFormatError as e:
                print(e)
                return Response({"detail": e.message}, status=400)
            return Response({"detail": resp})

        elif object_class is Statement:
            try:
                validate(request.data, STATEMENT_LIST)
            except JSONValidationError as e:
                return Response({"detail": e.message}, status=400)
            try:
                resp = ingest_statements(self.request.data, ipif_repo=ipif_repo)
            except DataFormatError as e:
                return Response({"detail": e.message}, status=400)
            return Response({"detail": resp})

        elif object_class is Source:
            try:
                validate(request.data, PERSON_SOURCE_LIST)
            except JSONValidationError as e:
                return Response({"detail": e.message}, status=400)
            try:
                resp = ingest_sources(self.request.data, ipif_repo=ipif_repo)
            except DataFormatError as e:
                return Response({"detail": e.message}, status=400)

            return Response({"detail": resp})

    return csrf_exempt(inner)


class BaseViewSet(viewsets.ViewSet):
    retrieve: Callable
    list: Callable
    post: Callable


def build_viewset(object_class: Type[IpifEntityAbstractBase]) -> Type[BaseViewSet]:
    viewset_name = f"{object_class.__name__}ViewSet"

    vs: Type[BaseViewSet] = type(
        viewset_name,
        (viewsets.ViewSet,),
        {
            "parser_classes": [JSONParser],
            # "authentication_classes": [BasicAuthentication],
            # "permission_classes": [IsAuthenticated],
            "post": post_view(object_class),
            "list": list_view(object_class),
            "retrieve": retrieve_view(object_class),
        },
    )
    return vs


# Construct these viewsets
PersonViewSet: Type[BaseViewSet] = build_viewset(Person)
SourceViewSet: Type[BaseViewSet] = build_viewset(Source)
FactoidViewSet: Type[BaseViewSet] = build_viewset(Factoid)
StatementViewSet: Type[BaseViewSet] = build_viewset(Statement)
