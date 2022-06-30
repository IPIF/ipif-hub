from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.shortcuts import render, redirect

from django_email_verification import send_email

from django.conf import settings


from ipif_hub.forms import IpifRepoForm, UserForm
from ipif_hub.models import IpifRepo


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


def create_ipif_repo(request, repo=None):
    if not request.user.is_authenticated:
        return redirect("%s?next=%s" % (settings.LOGIN_URL, request.path))

    if request.method == "POST":
        form = IpifRepoForm(request.POST)

        if form.is_valid():

            repo = IpifRepo(**form.cleaned_data)

            repo.save()
            repo.owners.add(request.user)
            repo.save()

    else:
        form = IpifRepoForm()

    return render(request, "ipif_hub/ipif_repo.html", {"form": form})


# def view_ipif_repos(request, repo=None):
