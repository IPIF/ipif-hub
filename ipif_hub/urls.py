from django.urls import path

from .api_views import FactoidViewSet, PersonViewSet, SourceViewSet, StatementViewSet
from .views import create_ipif_repo, ipif_repo_login

from .models import IpifRepo

urlpatterns = [
    path("persons/", PersonViewSet.as_view({"get": "list"})),
    path("persons/<path:pk>", PersonViewSet.as_view({"get": "retrieve"})),
    path("sources/", SourceViewSet.as_view({"get": "list"})),
    path("sources/<path:pk>", SourceViewSet.as_view({"get": "retrieve"})),
    path("factoids/", FactoidViewSet.as_view({"get": "list"})),
    path("factoids/<path:pk>", FactoidViewSet.as_view({"get": "retrieve"})),
    path("statements/", StatementViewSet.as_view({"get": "list"})),
    path("statements/<path:pk>", StatementViewSet.as_view({"get": "retrieve"})),
    path("repo/new", create_ipif_repo, name="new_repo"),
    path("repo/login", ipif_repo_login, name="repo_login"),
]
