from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path("", include("economy.urls")),
]

if settings.DJANGO_ADMIN_ENABLED:
    urlpatterns.append(path("admin/", admin.site.urls))
