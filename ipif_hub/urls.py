from django.urls import path

from .api_views import FactoidViewSet, PersonsViewSet, SourceViewSet, StatementViewSet

urlpatterns = [
    path("persons/", PersonsViewSet.as_view({"get": "list"})),
    path("persons/<path:pk>", PersonsViewSet.as_view({"get": "retrieve"})),
    path("sources/", SourceViewSet.as_view({"get": "list"})),
    path("sources/<path:pk>", SourceViewSet.as_view({"get": "retrieve"})),
    path("factoids/", FactoidViewSet.as_view({"get": "list"})),
    path("factoids/<path:pk>", FactoidViewSet.as_view({"get": "retrieve"})),
    path("statements/", StatementViewSet.as_view({"get": "list"})),
    path("statements/<path:pk>", StatementViewSet.as_view({"get": "retrieve"})),
]
