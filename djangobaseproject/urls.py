"""djangobaseproject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django_email_verification import urls as email_urls  # include the urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("webpage.urls", namespace="webpage")),
    path("infos/", include("infos.urls", namespace="infos")),
    path("ipif/", include("ipif_hub.api_urls")),
    path("<path:repo>/ipif/", include("ipif_hub.api_urls")),
    path("", include("ipif_hub.urls")),
    path("email/", include(email_urls)),  # connect them to an arbitrary path
]
handler404 = "webpage.views.handler404"
