import datetime
from urllib.parse import urlencode

import pytest
from django.db.models import Q
from pytest_django.asserts import assertNumQueries
from rest_framework import viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from ipif_hub.api_views import (
    FactoidViewSet,
    PersonViewSet,
    SourceViewSet,
    StatementViewSet,
    build_statement_filters,
    build_viewset,
    query_dict,
)
from ipif_hub.models import Factoid, MergePerson, MergeSource, Person, Source, Statement
from ipif_hub.serializers import (
    FactoidSerializer,
    MergePersonSerializer,
    MergeSourceSerializer,
    PersonSerializer,
    SourceSerializer,
    StatementSerializer,
)


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
def test_statement_retrieve_view_with_id_as_uri(statement, source, person, factoid):
    # The response data should be the same as this
    serialized_data = StatementSerializer(statement).data

    vs = StatementViewSet()

    req = build_request_with_params()

    response = vs.retrieve(request=req, pk=statement.identifier)
    assert isinstance(response, (Response,))

    # The response we get back is the same as was serialized
    assert response.data == serialized_data


@pytest.mark.django_db(transaction=True)
def test_factoid_retrieve_view_with_id_as_uri(statement, source, person, factoid):
    # The response data should be the same as this
    serialized_data = FactoidSerializer(factoid).data

    vs = FactoidViewSet()

    req = build_request_with_params()

    response = vs.retrieve(request=req, pk=statement.identifier)
    assert isinstance(response, (Response,))

    # The response we get back is the same as was serialized
    print(response.data)
    assert response.data == serialized_data


@pytest.mark.django_db(transaction=True)
def test_person_retrieve_view_returns_merge_person(source, statement, factoid, person):
    serialized_data = MergePersonSerializer(person.merge_person.first()).data

    vs = PersonViewSet()

    req = build_request_with_params()

    response = vs.retrieve(request=req, pk=person.identifier)

    assert isinstance(response, (Response,))

    assert response.data == serialized_data


@pytest.mark.django_db(transaction=True)
def test_source_retrieve_view_returns_merge_source(source, statement, factoid, person):
    serialized_data = MergeSourceSerializer(source.merge_source.first()).data

    vs = SourceViewSet()

    req = build_request_with_params()

    response = vs.retrieve(request=req, pk=source.identifier)

    assert isinstance(response, (Response,))

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
def test_list_view_with_id_params_raises_error_when_id_and_no_repo(factoid, person):
    vs = PersonViewSet()

    req = build_request_with_params(sourceId="source1")
    response = vs.list(request=req)
    assert response.status_code == 400

    req = build_request_with_params(sourceId="source1")
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_retrieve_view_with_alternative_uri_and_repo(person, factoid):
    # The response data should be the same as this
    serialized_data = PersonSerializer(person).data

    vs = PersonViewSet()

    req = build_request_with_params()

    response = vs.retrieve(
        request=req, pk="http://alternative.com/person1", repo="testrepo"
    )
    assert isinstance(response, (Response,))

    # The response we get back is the same as was serialized
    assert response.data == serialized_data


# TODO: DUPLICATE THIS TEST FOR SOURCE!


@pytest.mark.django_db(transaction=True)
def test_retrieve_view_with_alternative_uri_returns_merge_person(
    person: Person, factoid: Factoid
):
    # The response data should be the same as this
    serialized_data = MergePersonSerializer(person.merge_person.first()).data

    vs = PersonViewSet()

    req = build_request_with_params()

    response = vs.retrieve(request=req, pk="http://alternative.com/person1")
    assert isinstance(response, (Response,))

    # The response we get back is the same as was serialized
    assert response.data == serialized_data


@pytest.mark.django_db(transaction=True)
def test_retrieve_view_with_alternative_uri_returns_merge_source(
    source: Source, factoid: Factoid
):
    # The response data should be the same as this
    serialized_data = MergeSourceSerializer(source.merge_source.first()).data

    vs = SourceViewSet()

    req = build_request_with_params()

    response = vs.retrieve(request=req, pk="http://sources.com/source1")
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
def test_list_view_basic_returns_item_with_repo(person, factoid, statement, source):
    vs = PersonViewSet()
    req = build_request_with_params()

    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200

    # This implicitly tests that the autocreated relatesTo person
    # (see conftest.statement) is not returned
    assert response.data == [PersonSerializer(person).data]

    vs = FactoidViewSet()
    req = build_request_with_params()
    with assertNumQueries(0):
        response = vs.list(request=req, repo="testrepo")

    assert response.status_code == 200
    assert response.data == [FactoidSerializer(factoid).data]

    # Factoid should also return with no repo
    req = build_request_with_params()
    with assertNumQueries(0):
        response = vs.list(request=req)

    assert response.status_code == 200
    assert response.data == [FactoidSerializer(factoid).data]

    vs = StatementViewSet()
    req = build_request_with_params()
    with assertNumQueries(0):
        response = vs.list(request=req, repo="testrepo")

    assert response.status_code == 200
    assert response.data == [StatementSerializer(statement).data]

    # Statements should also return with no repo
    req = build_request_with_params()
    with assertNumQueries(0):
        response = vs.list(request=req)

    assert response.status_code == 200
    assert response.data == [StatementSerializer(statement).data]

    vs = SourceViewSet()
    req = build_request_with_params()
    with assertNumQueries(0):
        response = vs.list(request=req, repo="testrepo")

    assert response.status_code == 200
    assert response.data == [SourceSerializer(source).data]


@pytest.mark.django_db(transaction=True)
def test_list_view_person_basic_returns_merge_person(
    person, factoid, statement, source
):
    serialized_data = MergePersonSerializer(MergePerson.objects.all(), many=True).data

    vs: PersonViewSet = PersonViewSet()
    req = build_request_with_params()

    response = vs.list(request=req)
    assert response.status_code == 200
    assert response.data == serialized_data


@pytest.mark.django_db(transaction=True)
def test_list_view_source_basic_returns_merge_source(
    person, factoid, statement, source
):
    serialized_data = MergeSourceSerializer(MergeSource.objects.all(), many=True).data

    vs: SourceViewSet = SourceViewSet()
    req = build_request_with_params()

    response = vs.list(request=req)
    assert response.status_code == 200
    assert response.data == serialized_data


@pytest.mark.django_db(transaction=True)
def test_list_view_basic_returns_item_with_full_text(person, factoid):

    vs = PersonViewSet()

    req = build_request_with_params(p="researcher1")

    with assertNumQueries(0):
        response = vs.list(request=req, repo="testrepo")

    assert response.status_code == 200
    assert response.data == [PersonSerializer(person).data]

    req = build_request_with_params(st="Smith")
    with assertNumQueries(0):
        response = vs.list(request=req, repo="testrepo")

    assert response.status_code == 200
    assert response.data == [PersonSerializer(person).data]

    req = build_request_with_params(s="researcher2")
    with assertNumQueries(0):
        response = vs.list(request=req, repo="testrepo")

    assert response.status_code == 200
    assert response.data == [PersonSerializer(person).data]

    # Now factoids...
    vs = FactoidViewSet()
    req = build_request_with_params(p="researcher1")
    with assertNumQueries(0):
        response = vs.list(request=req)

    assert response.status_code == 200
    assert response.data == [FactoidSerializer(factoid).data]


@pytest.mark.django_db(transaction=True)
def test_list_view_basic_returns_merge_person_with_full_text(person, factoid):

    vs = PersonViewSet()

    req = build_request_with_params(p="researcher1")

    with assertNumQueries(0):
        response = vs.list(request=req)

    assert response.status_code == 200
    assert response.data == [MergePersonSerializer(person.merge_person.first()).data]


@pytest.mark.django_db(transaction=True)
def test_list_view_basic_returns_merge_source_with_full_text(person, factoid, source):

    vs = SourceViewSet()

    req = build_request_with_params(p="researcher1")

    with assertNumQueries(0):
        response = vs.list(request=req)

    assert response.status_code == 200
    assert response.data == [MergeSourceSerializer(source.merge_source.first()).data]


@pytest.mark.django_db(transaction=True)
def test_list_view_sort_by(person, person2, factoid):
    vs = PersonViewSet()
    req = build_request_with_params()

    response = vs.list(request=req, repo="test_repo")
    assert response.status_code == 200
    assert response.data == [
        PersonSerializer(person2).data,
        PersonSerializer(person).data,
    ]

    req = build_request_with_params(sortBy="personId ASC")

    response = vs.list(request=req, repo="test_repo")
    assert response.status_code == 200
    assert response.data == [
        PersonSerializer(person).data,
        PersonSerializer(person2).data,
    ]

    req = build_request_with_params(sortBy="personId DESC")

    response = vs.list(request=req, repo="test_repo")
    assert response.status_code == 200
    assert response.data == [
        PersonSerializer(person2).data,
        PersonSerializer(person).data,
    ]


@pytest.mark.django_db(transaction=True)
def test_list_view_merge_person_sort_by(
    person: Person,
    personNotSameAs: Person,
    factoid,
    factoid2,
    source,
    statement,
    statement2,
    factoid4,
):
    vs = PersonViewSet()
    req = build_request_with_params()

    response = vs.list(request=req)
    assert response.status_code == 200
    print(response.data)
    print(MergePerson.objects.all())

    assert response.data == [
        MergePersonSerializer(person.merge_person.first()).data,
        MergePersonSerializer(personNotSameAs.merge_person.first()).data,
    ]

    req = build_request_with_params(sortBy="personId ASC")

    response = vs.list(request=req)
    assert response.status_code == 200
    assert response.data == [
        MergePersonSerializer(person.merge_person.first()).data,
        MergePersonSerializer(personNotSameAs.merge_person.first()).data,
    ]

    req = build_request_with_params(sortBy="personId DESC")

    response = vs.list(request=req)
    assert response.status_code == 200
    assert response.data == [
        MergePersonSerializer(personNotSameAs.merge_person.first()).data,
        MergePersonSerializer(person.merge_person.first()).data,
    ]


@pytest.mark.django_db(transaction=True)
def test_list_view_merge_source_sort_by(
    sourceNotSameAs: Source,
    source: Source,
    person: Person,
    personNotSameAs: Person,
    factoid,
    factoid2,
    statement,
    statement2,
    factoid4,
):
    vs = SourceViewSet()
    req = build_request_with_params()

    response = vs.list(request=req)
    assert response.status_code == 200
    print(response.data)
    print("---")
    print(
        MergeSourceSerializer(source.merge_source.first()).data,
    )

    assert response.data == [
        MergeSourceSerializer(sourceNotSameAs.merge_source.first()).data,
        MergeSourceSerializer(source.merge_source.first()).data,
    ]
    """
    req = build_request_with_params(sortBy="personId ASC")

    response = vs.list(request=req)
    assert response.status_code == 200
    assert response.data == [
        MergePersonSerializer(person.merge_person.first()).data,
        MergePersonSerializer(personNotSameAs.merge_person.first()).data,
    ]

    req = build_request_with_params(sortBy="personId DESC")

    response = vs.list(request=req)
    assert response.status_code == 200
    assert response.data == [
        MergePersonSerializer(personNotSameAs.merge_person.first()).data,
        MergePersonSerializer(person.merge_person.first()).data,
    ]


@pytest.mark.django_db(transaction=True)
def test_list_view_pagination(person, person2, factoid):
    vs = PersonViewSet()

    req = build_request_with_params(size=1, page=1, sortBy="personId")
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert response.data == [
        PersonSerializer(person).data,
    ]

    req = build_request_with_params(size=1, page=2, sortBy="personId")
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert response.data == [
        PersonSerializer(person2).data,
    ]

    req = build_request_with_params(size=2, page=1, sortBy="personId")
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert response.data == [
        PersonSerializer(person).data,
        PersonSerializer(person2).data,
    ]
    """


@pytest.mark.django_db(transaction=True)
def test_list_view_with_id_query_params(person, factoid, statement):
    vs = PersonViewSet()

    req = build_request_with_params(statementId="http://test.com/statements/statement1")
    with assertNumQueries(1):
        response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert response.data == [PersonSerializer(person).data]

    # Now try it matching nothing to make sure the filter works
    req = build_request_with_params(statementId="http://nomatch.com/statement")
    with assertNumQueries(1):
        response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert response.data == []

    vs = StatementViewSet()
    req = build_request_with_params(personId="http://test.com/persons/person1")
    with assertNumQueries(1):
        response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert response.data == [StatementSerializer(statement).data]

    # Now try it matching nothing to make sure the filter works
    vs = StatementViewSet()
    req = build_request_with_params(personId="http://nomatch.com/person")
    with assertNumQueries(1):
        response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert response.data == []

    vs = StatementViewSet()
    req = build_request_with_params(factoidId="http://test.com/factoids/factoid1")
    with assertNumQueries(1):
        response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert response.data == [StatementSerializer(statement).data]

    # Now try it matching nothing to make sure the filter works
    vs = StatementViewSet()
    req = build_request_with_params(factoidId="http://nomatch.com/factoid")
    with assertNumQueries(1):
        response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert response.data == []

    vs = StatementViewSet()
    req = build_request_with_params(sourceId="http://test.com/sources/source1")
    with assertNumQueries(1):
        response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert response.data == [StatementSerializer(statement).data]

    # Now try it matching nothing to make sure the filter works
    vs = StatementViewSet()
    req = build_request_with_params(sourceId="http://nomatch.com/source")

    with assertNumQueries(1):
        response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db(transaction=True)
def test_list_view_with_id_query_params_on_merge_person(
    person, factoid, statement, source
):
    # TODO: Might need to test this more, but since it's really a simple join,
    # to something that already works, maybe it's not necessary?
    vs = PersonViewSet()

    merge_person = MergePerson.objects.first()

    # Check that a MergePerson object actually exists
    assert merge_person

    req = build_request_with_params(statementId="http://test.com/statements/statement1")
    with assertNumQueries(1):
        response = vs.list(request=req)
    assert response.status_code == 200
    assert response.data == [MergePersonSerializer(merge_person).data]

    # Now try it matching nothing to make sure the filter works
    req = build_request_with_params(statementId="http://nomatch.com/statement")
    with assertNumQueries(1):
        response = vs.list(request=req)
    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db(transaction=True)
def test_list_view_with_id_params_works_with_local_id_and_repo(factoid, person):
    vs = PersonViewSet()

    req = build_request_with_params(statementId="statement1")
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert response.data == [PersonSerializer(person).data]

    req = build_request_with_params(sourceId="source1")
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert response.data == [PersonSerializer(person).data]

    req = build_request_with_params(factoidId="factoid1")
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert response.data == [PersonSerializer(person).data]

    req = build_request_with_params(personId="person1")
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert response.data == [PersonSerializer(person).data]


@pytest.mark.django_db(transaction=True)
def test_list_view_statement_params_on_statement(
    factoid,
    factoid2,
    statement,
    statement2,
):
    vs = StatementViewSet()

    # Quick sanity test that we get both statements
    req = build_request_with_params(orderBy="statementId")
    response = vs.list(request=req)
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data == [
        StatementSerializer(statement).data,
        StatementSerializer(statement2).data,
    ]

    req = build_request_with_params(name="John Smith")
    response = vs.list(request=req)
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data == [
        StatementSerializer(statement).data,
    ]

    req = build_request_with_params(name="Johannes Schmitt")
    response = vs.list(request=req)
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data == [
        StatementSerializer(statement2).data,
    ]


@pytest.mark.django_db(transaction=True)
def test_list_view_statement_params_on_person_match_all(
    factoid, factoid2, statement, statement2, person
):
    vs = PersonViewSet()

    # Sanity check does match with real match
    req = build_request_with_params(role="unemployed")
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data == [PersonSerializer(person).data]

    # Sanity check does not match
    req = build_request_with_params(role="DOES_NOT_MATCH")
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert len(response.data) == 0
    assert response.data == []

    # Ok, real test now
    # This is the default —— all apply to same statement, hence this should
    # return nothing
    req = build_request_with_params(role="unemployed", name="Johannes Schmitt")
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert len(response.data) == 0
    assert response.data == []

    # Now, with independentStatements="matchAll", it should match both params,
    # but they can be part of separate statements
    req = build_request_with_params(
        role="unemployed", name="Johannes Schmitt", independentStatements="matchAll"
    )
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data == [PersonSerializer(person).data]

    # Now this one should fail as *both* params need to match at least one
    # related Statement
    req = build_request_with_params(
        role="DOES_NOT_MATCH", name="Johannes Schmitt", independentStatements="matchAll"
    )
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert len(response.data) == 0
    assert response.data == []

    # Finally, this one should pass as only one of the params needs to match a statement
    req = build_request_with_params(
        role="DOES_NOT_MATCH", name="Johannes Schmitt", independentStatements="matchAny"
    )
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data == [PersonSerializer(person).data]


@pytest.mark.django_db(transaction=True)
def test_params_query_correctly(factoid, statement, person):
    vs = PersonViewSet()

    req = build_request_with_params(_from=1800, to=1899)
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert len(response.data) == 0
    assert response.data == []

    req = build_request_with_params(_from=1899, to=1999)
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data == [PersonSerializer(person).data]

    req = build_request_with_params(statementText="DOES_NOT_MATCH")
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert len(response.data) == 0
    assert response.data == []

    req = build_request_with_params(statementText="Member")
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data == [PersonSerializer(person).data]

    req = build_request_with_params(role="DOES_NOT_MATCH")
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert len(response.data) == 0
    assert response.data == []

    req = build_request_with_params(role="unemployed")
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data == [PersonSerializer(person).data]

    req = build_request_with_params(place="DOES_NOT_MATCH")
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert len(response.data) == 0
    assert response.data == []

    req = build_request_with_params(place="Nowhere")
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data == [PersonSerializer(person).data]

    req = build_request_with_params(memberOf="DOES_NOT_MATCH")
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert len(response.data) == 0
    assert response.data == []

    req = build_request_with_params(memberOf="http://orgs.com/madeup")
    response = vs.list(request=req, repo="testrepo")
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data == [PersonSerializer(person).data]
