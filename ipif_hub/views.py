import json

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views import View
from django_email_verification import send_email

from django.conf import settings

from rest_framework import views as DRF_views
from rest_framework import parsers as DRF_parsers
from rest_framework import response as DRF_response

from jsonschema import ValidationError, validate


from ipif_hub.forms import IpifRepoForm, UserForm
from ipif_hub.management.utils.ingest_schemas import FLAT_LIST_SCHEMA
from ipif_hub.models import IpifRepo

from ipif_hub.management.utils.ingest_data import ingest_data
from ipif_hub.tasks import ingest_json_data_task


class IpifRepoCreateView(View):
    def get(self, request):
        print(request.user.is_active, "is active")
        if not request.user.is_authenticated:
            return redirect("%s?next=%s" % (settings.LOGIN_URL, request.path))

        form = IpifRepoForm()
        return render(
            request,
            "ipif_hub/ipif_repo/create.html",
            {"form": form, "submit_path": "/repo/new"},
        )

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect("%s?next=%s" % (settings.LOGIN_URL, request.path))

        form = IpifRepoForm(request.POST)

        if form.is_valid():
            repo = IpifRepo(**form.cleaned_data)
            repo.save()
            repo.owners.add(request.user)
            repo.save()
            messages.add_message(
                request, messages.INFO, f"IPIF repository {repo.endpoint_name} created."
            )
            return redirect("view_repo", pk=repo.pk)


class IpifRepoView(View):
    def get(self, request, pk=None, created=False):
        repo = IpifRepo.objects.get(pk=pk)
        return render(request, "ipif_hub/ipif_repo/view.html", {"repo": repo})


class IpifRepoListView(View):
    def get(self, request):
        print("called")
        repos = IpifRepo.objects.exclude(pk="IPIFHUB_AUTOCREATED")
        return render(request, "ipif_hub/ipif_repo/list.html", {"repos": repos})


class IpifRepoEditView(View):
    def get(self, request, pk=None):
        if not request.user.is_authenticated:
            return redirect("%s?next=%s" % (settings.LOGIN_URL, request.path))

        repo = IpifRepo.objects.get(pk=pk)
        if not request.user in repo.owners.all():
            messages.add_message(
                request,
                messages.ERROR,
                f"You do not have permission to edit this repository.",
            )
            return redirect("view_repo", pk=repo.pk)

        form = IpifRepoForm(instance=repo)
        return render(
            request,
            "ipif_hub/ipif_repo/create.html",
            {"form": form, "submit_path": f"/repo/{repo.pk}/edit/"},
        )

    def post(self, request, pk=None):
        if not request.user.is_authenticated:
            return redirect("%s?next=%s" % (settings.LOGIN_URL, request.path))

        repo = IpifRepo.objects.get(pk=pk)

        if not request.user in repo.owners.all():
            messages.add_message(
                request,
                messages.ERROR,
                f"You do not have permission to edit this repository.",
            )
            return redirect("view_repo", pk=repo.pk)

        form = IpifRepoForm(request.POST, instance=repo)

        if form.is_valid():

            form.save()
            # repo.save()
            messages.add_message(
                request, messages.INFO, f"IPIF repository {repo.endpoint_name} saved."
            )
            return redirect("view_repo", pk=repo.pk)

        return redirect("view_repo", pk=repo.pk)


def create_user(request):

    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            _ = form.cleaned_data.pop("confirm_password")
            user = User(**form.cleaned_data)
            user.set_password(form.cleaned_data["password"])
            user.is_active = False
            user.save()
            send_email(user)
            return render(request, "ipif_hub/created_user.html", {"user": user})
    else:
        form = UserForm()
    return render(request, "ipif_hub/create_user.html", {"form": form})


class BatchUpload(DRF_views.APIView):
    parser_classes = [DRF_parsers.MultiPartParser, DRF_parsers.FileUploadParser]

    def post(self, request, pk=None, fname=None):

        repo = IpifRepo.objects.get(pk=pk)

        if request.user not in repo.owners.all():
            return DRF_response.Response(
                {"detail": "You do not have permission to push to this endpoint"},
                status=403,
            )

        f = request.FILES["file"]

        try:
            data = json.loads(f.read())
            validate(data, schema=FLAT_LIST_SCHEMA)
        except json.JSONDecodeError as e:
            return DRF_response.Response(
                {"detail": "Uploaded file is not parseable as JSON"}, status=400
            )
        except ValidationError as e:
            return DRF_response.Response({"detail": e.message}, status=400)

        ingest_json_data_task.delay(pk, data)

        return DRF_response.Response(
            {
                "detail": "Upload completed. Ingesting data.",
            },
            status=201,
        )
