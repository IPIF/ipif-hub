from django.urls import path

from .api_views import FactoidViewSet, PersonViewSet, SourceViewSet, StatementViewSet
from .views import create_ipif_repo, create_user

from .models import IpifRepo

urlpatterns = [
    path("repo/new", create_ipif_repo, name="new_repo"),
    path("user/new", create_user, name="create_user"),
]
