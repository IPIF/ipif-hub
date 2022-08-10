import datetime
import json
from typing import Dict
from urllib.parse import urlencode

import pytest
from pytest_django.asserts import assertNumQueries

from django.db.models import Q
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework import viewsets

from ipif_hub.api_views import (
    FactoidViewSet,
    SourceViewSet,
    StatementViewSet,
    build_statement_filters,
    build_viewset,
    query_dict,
    PersonViewSet,
)
from ipif_hub.models import Factoid, Person, Source, Statement
from ipif_hub.serializers import (
    FactoidSerializer,
    PersonSerializer,
    SourceSerializer,
    StatementSerializer,
)
from ipif_hub.tests.conftest import factoid, person, source, statement


def build_request_with_params(**params) -> Request:
    """Builds a Request object using query_params"""

    if "_from" in params:
        params["from"] = params.pop("_from")

    factory = APIRequestFactory()
    temp_get_request = factory.get(f"/?{urlencode(params)}")
    req = Request(temp_get_request)
    return req


def test_build_statement_filters_name():
    req = build_request_with_params(name="John")
    statement_filters = build_statement_filters(req)
    assert statement_filters == [Q(name="John")]


def test_build_statement_filters_role():
    req = build_request_with_params(role="janitor")
    statement_filters = build_statement_filters(req)
    assert statement_filters == [Q(role_uri="janitor") | Q(role_label="janitor")]


def test_build_statement_filters_memberOf():
    req = build_request_with_params(memberOf="http://orgs.com/bank")
    statement_filters = build_statement_filters(req)
    assert statement_filters == [
        Q(memberOf_uri="http://orgs.com/bank")
        | Q(memberOf_label="http://orgs.com/bank")
    ]


def test_build_statement_filters_place():
    req = build_request_with_params(place="Gibraltar")
    statement_filters = build_statement_filters(req)
    assert statement_filters == [
        Q(places__uri="Gibraltar") | Q(places__label="Gibraltar")
    ]


def test_build_statement_filters_relatesToPerson():
    req = build_request_with_params(relatesToPerson="John")
    statement_filters = build_statement_filters(req)
    assert statement_filters == [
        Q(relatesToPerson__uris__uri="John") | Q(relatesToPerson__id="John")
    ]


def test_build_statement_filters_dates():
    req = build_request_with_params(_from="1900", to="2000-10-01")
    statement_filters = build_statement_filters(req)
    assert statement_filters == [
        Q(date_sortdate__gte=datetime.date(1900, 1, 1)),
        Q(date_sortdate__lte=datetime.date(2000, 10, 1)),
    ]


def test_build_statement_filters_multiple():
    req = build_request_with_params(
        _from="1900", to="2000-10-01", name="John", place="Gibraltar"
    )
    statement_filters = build_statement_filters(req)
    assert statement_filters == [
        Q(name="John"),
        Q(places__uri="Gibraltar") | Q(places__label="Gibraltar"),
        Q(date_sortdate__gte=datetime.date(1900, 1, 1)),
        Q(date_sortdate__lte=datetime.date(2000, 10, 1)),
    ]


def test_query_dict():
    # Dealing with Factoid directly (no path)
    assert query_dict("")("statement__name", "John") == {"statement__name": "John"}
    # Dealing with any other type (path via factoid)
    assert query_dict("factoid__")("statement__name", "John") == {
        "factoid__statement__name": "John"
    }


def test_build_viewset():
    VS = build_viewset(Person)
    assert VS.__name__ == "PersonViewSet"
    assert issubclass(VS, (viewsets.ViewSet,))

    VS = build_viewset(Factoid)
    assert VS.__name__ == "FactoidViewSet"

    VS = build_viewset(Source)
    assert VS.__name__ == "SourceViewSet"

    VS = build_viewset(Statement)
    assert VS.__name__ == "StatementViewSet"


@pytest.mark.django_db(transaction=True)
def test_retrieve_view_with_id_as_uri(person, factoid):
    # The response data should be the same as this
    serialized_data = PersonSerializer(person).data

    vs = PersonViewSet()

    req = build_request_with_params()

    response = vs.retrieve(request=req, pk=person.pk)
    assert isinstance(response, (Response,))

    # The response we get back is the same as was serialized
    assert response.data == serialized_data


@pytest.mark.django_db(transaction=True)
def test_retrieve_view_with_local_id_and_repo(person, factoid):
    # The response data should be the same as this
    serialized_data = PersonSerializer(person).data

    vs = PersonViewSet()

    req = build_request_with_params()

    response = vs.retrieve(request=req, pk=person.local_id, repo="testrepo")
    assert isinstance(response, (Response,))

    # The response we get back is the same as was serialized
    assert response.data == serialized_data


@pytest.mark.django_db(transaction=True)
def test_retrieve_view_with_alternative_uri(person, factoid):
    # The response data should be the same as this
    serialized_data = PersonSerializer(person).data

    vs = PersonViewSet()

    req = build_request_with_params()

    response = vs.retrieve(request=req, pk="http://alternative.com/person1")
    assert isinstance(response, (Response,))

    # The response we get back is the same as was serialized
    assert response.data == serialized_data


@pytest.mark.django_db(transaction=True)
def test_retrieve_view_fails_with_non_uri_id_and_no_repo(person, factoid):
    vs = PersonViewSet()
    req = build_request_with_params()

    response = vs.retrieve(request=req, pk="a_local_id")
    assert response.status_code == 400
    assert response.data == {
        "detail": (
            "Either query a specific dataset using"
            " the dataset-specific route, or provide a full URI as identifier"
        )
    }


"""
N.B. assertNumQueries(0) context manager is used below to check that none
of the queries hit the Django database —— all work should be done with
Solr indices
"""


@pytest.mark.django_db(transaction=True)
def test_list_view_basic_returns_item(person, factoid, statement, source):
    vs = PersonViewSet()
    req = build_request_with_params()

    response = vs.list(request=req)
    assert response.status_code == 200

    # This implicitly tests that the autocreated relatesTo person
    # (see conftest.statement) is not returned
    assert response.data == [PersonSerializer(person).data]

    vs = FactoidViewSet()
    req = build_request_with_params()
    with assertNumQueries(0):
        response = vs.list(request=req)

    assert response.status_code == 200
    assert response.data == [FactoidSerializer(factoid).data]

    vs = StatementViewSet()
    req = build_request_with_params()
    with assertNumQueries(0):
        response = vs.list(request=req)

    assert response.status_code == 200
    assert response.data == [StatementSerializer(statement).data]

    vs = SourceViewSet()
    req = build_request_with_params()
    with assertNumQueries(0):
        response = vs.list(request=req)

    assert response.status_code == 200
    assert response.data == [SourceSerializer(source).data]


@pytest.mark.django_db(transaction=True)
def test_list_view_basic_returns_item_with_full_text(person, factoid):

    vs = PersonViewSet()

    req = build_request_with_params(p="researcher1")

    with assertNumQueries(0):
        response = vs.list(request=req)

    assert response.status_code == 200
    assert response.data == [PersonSerializer(person).data]

    req = build_request_with_params(st="Smith")
    with assertNumQueries(0):
        response = vs.list(request=req)

    assert response.status_code == 200
    assert response.data == [PersonSerializer(person).data]

    req = build_request_with_params(s="researcher2")
    with assertNumQueries(0):
        response = vs.list(request=req)

    assert response.status_code == 200
    assert response.data == [PersonSerializer(person).data]

    # Now factoids...
    vs = FactoidViewSet()
    req = build_request_with_params(p="researcher1")
    with assertNumQueries(0):
        response = vs.list(request=req)

    assert response.status_code == 200
    assert response.data == [FactoidSerializer(factoid).data]
