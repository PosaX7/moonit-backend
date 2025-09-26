from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", lambda request: HttpResponse("Bienvenue sur l'API NoTiMo")),
    path("api/auth/", include("users.urls")),
    path("api/", include("transactions.urls")),
]
