from django.contrib import admin
from django.urls import include, path

urlpatterns = [
        path("play/", include("play.urls")),
        path("admin/", admin.site.urls),
]
