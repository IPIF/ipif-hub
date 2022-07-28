from django.urls import path

from .api_views import FactoidViewSet, PersonViewSet, SourceViewSet, StatementViewSet
from .views import IpifRepoCreateView, IpifRepoView, create_user, IpifRepoListView

from .models import IpifRepo

urlpatterns = [
    path("repo/new/", IpifRepoCreateView.as_view()),
    path("repo/<str:pk>/", IpifRepoView.as_view(), name="view_repo"),
    path("repo/", IpifRepoListView.as_view(), name="view_repo_list"),
    path("user/new/", create_user, name="create_user"),
]
