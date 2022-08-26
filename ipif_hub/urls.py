from django.urls import path

from ipif_hub.views import (
    BatchUpload,
    IngestionJobView,
    IpifRepoCreateView,
    IpifRepoEditView,
    IpifRepoListView,
    IpifRepoView,
    create_user,
)

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
