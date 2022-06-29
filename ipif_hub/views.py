from django.shortcuts import render

from ipif_hub.forms import IpifRepoForm
from ipif_hub.models import IpifRepo


def create_ipif_repo(request):
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
