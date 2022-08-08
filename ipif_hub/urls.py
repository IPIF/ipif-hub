from crypt import methods
from django.urls import path

from .views import (
    IpifRepoCreateView,
    IpifRepoView,
    create_user,
    IpifRepoListView,
    IpifRepoEditView,
    BatchUpload,
    IngestionJobView,
)

from .models import IpifRepo

urlpatterns = [
    path("repo/new/", IpifRepoCreateView.as_view()),
    path(
        "repo/<str:pk>/data/",
        BatchUpload.as_view(),
        name="batch_upload",
    ),
    path("repo/<str:pk>/", IpifRepoView.as_view(), name="view_repo"),
    path("repo/<str:pk>/edit/", IpifRepoEditView.as_view(), name="edit_repo"),
    path("repo/", IpifRepoListView.as_view(), name="view_repo_list"),
    path("job/<str:pk>/", IngestionJobView.as_view(), name="view_job"),
    path("user/new/", create_user, name="create_user"),
]
