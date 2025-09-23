from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet, solde

router = DefaultRouter()
router.register(r"transactions", TransactionViewSet, basename="transaction")

urlpatterns = [
    path("", include(router.urls)),
    path("solde/", solde, name="solde"),
]
