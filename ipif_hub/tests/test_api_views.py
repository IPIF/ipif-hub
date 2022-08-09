import datetime
from typing import Dict
from urllib.parse import urlencode

import pytest

from django.db.models import Q
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from ipif_hub.api_views import build_statement_filters, query_dict


def build_request(**params) -> Request:
    """Builds a Request object using query_params"""

    if "_from" in params:
        params["from"] = params.pop("_from")

    factory = APIRequestFactory()
    temp_get_request = factory.get(f"/?{urlencode(params)}")
    req = Request(temp_get_request)
    return req


def test_build_statement_filters_name():
    req = build_request(name="John")
    statement_filters = build_statement_filters(req)
    assert statement_filters == [Q(name="John")]


def test_build_statement_filters_role():
    req = build_request(role="janitor")
    statement_filters = build_statement_filters(req)
    assert statement_filters == [Q(role_uri="janitor") | Q(role_label="janitor")]


def test_build_statement_filters_memberOf():
    req = build_request(memberOf="http://orgs.com/bank")
    statement_filters = build_statement_filters(req)
    assert statement_filters == [
        Q(memberOf_uri="http://orgs.com/bank")
        | Q(memberOf_label="http://orgs.com/bank")
    ]


def test_build_statement_filters_place():
    req = build_request(place="Gibraltar")
    statement_filters = build_statement_filters(req)
    assert statement_filters == [
        Q(places__uri="Gibraltar") | Q(places__label="Gibraltar")
    ]


def test_build_statement_filters_relatesToPerson():
    req = build_request(relatesToPerson="John")
    statement_filters = build_statement_filters(req)
    assert statement_filters == [
        Q(relatesToPerson__uris__uri="John") | Q(relatesToPerson__id="John")
    ]


def test_build_statement_filters_dates():
    req = build_request(_from="1900", to="2000-10-01")
    statement_filters = build_statement_filters(req)
    assert statement_filters == [
        Q(date_sortdate__gte=datetime.date(1900, 1, 1)),
        Q(date_sortdate__lte=datetime.date(2000, 10, 1)),
    ]


def test_build_statement_filters_multiple():
    req = build_request(_from="1900", to="2000-10-01", name="John", place="Gibraltar")
    statement_filters = build_statement_filters(req)
    assert statement_filters == [
        Q(name="John"),
        Q(places__uri="Gibraltar") | Q(places__label="Gibraltar"),
        Q(date_sortdate__gte=datetime.date(1900, 1, 1)),
        Q(date_sortdate__lte=datetime.date(2000, 10, 1)),
    ]
