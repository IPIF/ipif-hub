from django.urls import path

from ipif_hub.api_views import (
    FactoidViewSet,
    PersonViewSet,
    SourceViewSet,
    StatementViewSet,
)

urlpatterns = [
    path("persons/", PersonViewSet.as_view({"get": "list"})),
    path("persons/<path:pk>", PersonViewSet.as_view({"get": "retrieve"})),
    path("sources/", SourceViewSet.as_view({"get": "list"})),
    path("sources/<path:pk>", SourceViewSet.as_view({"get": "retrieve"})),
    path("factoids/", FactoidViewSet.as_view({"get": "list"})),
    path("factoids/<path:pk>", FactoidViewSet.as_view({"get": "retrieve"})),
    path("statements/", StatementViewSet.as_view({"get": "list"})),
    path("statements/<path:pk>", StatementViewSet.as_view({"get": "retrieve"})),
]
