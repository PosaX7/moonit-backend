from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.views import register

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", lambda request: HttpResponse("Bienvenue sur l'API NoTiMo")),
    
    # Authentification
    path("api/auth/", include("users.urls")),
    path("api/register/", register, name="register"),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    
    # Transactions
    path("api/transactions/", include("transactions.urls")),  # ✅ plus propre
]
