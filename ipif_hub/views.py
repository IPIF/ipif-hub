from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from django_email_verification import send_email

from django.conf import settings


from ipif_hub.forms import IpifRepoForm, UserForm
from ipif_hub.models import IpifRepo


class IpifRepoCreateView(View):
    def get(self, request):
        print(request.user.is_active, "is active")
        if not request.user.is_authenticated:
            return redirect("%s?next=%s" % (settings.LOGIN_URL, request.path))

        form = IpifRepoForm()
        return render(request, "ipif_hub/ipif_repo/create.html", {"form": form})

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

        form = IpifRepoForm()
        return render(request, "ipif_hub/ipif_repo/create.html", {"form": form})

    def post(self, request, pk=None):
        if not request.user.is_authenticated:
            return redirect("%s?next=%s" % (settings.LOGIN_URL, request.path))

        form = IpifRepoForm(request.POST)

        if form.is_valid():
            repo = IpifRepo(**form.cleaned_data)
            repo.save()
            repo.owners.add(request.user)
            repo.save()
            messages.add_message(
                request, messages.INFO, f"IPIF repository {repo.endpoint_name} saved."
            )
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


# def view_ipif_repos(request, repo=None):
