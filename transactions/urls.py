from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet, CategorieViewSet

router = DefaultRouter()
router.register('categories', CategorieViewSet, basename='categories')
router.register('', TransactionViewSet, basename='transactions')  # ✅ route vide

urlpatterns = router.urls
