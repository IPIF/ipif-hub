from django.shortcuts import render

from ipif_hub.forms import IpifRepoForm, IpifRepoLogin
from ipif_hub.models import IpifRepo


def create_ipif_repo(request, repo=None):
    if repo:
        raise Exception("CAN'T CREATE NEW FROM HERE")
    if request.method == "POST":
        form = IpifRepoForm(request.POST)

        if form.is_valid():
            _ = form.cleaned_data.pop("confirm_password")

            repo = IpifRepo(**form.cleaned_data)
            repo.set_password(form.cleaned_data["password"])
            repo.save()

    else:
        form = IpifRepoForm()

    return render(request, "ipif_hub/ipif_repo.html", {"form": form})


def ipif_repo_login(request, repo=None):
    if request.method == "POST":
        form = IpifRepoLogin(request.POST)

    else:
        try:
            repo = IpifRepo.objects.get(pk=repo)

        except IpifRepo.DoesNotExist:
            raise Exception("no such repo")

        form = IpifRepoLogin()

    return render(request, "ipif_hub/ipif_repo_login.html", {"form": form})
