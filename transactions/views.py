from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum
from .models import Transaction
from .serializers import TransactionSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    """
    Gestion des transactions de l'utilisateur connecté.
    Inclut la création, lecture, mise à jour et suppression.
    Filtrage par module : 'suivi' ou 'budget'.
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        module = self.request.query_params.get("module")  # 'suivi' ou 'budget'
        qs = Transaction.objects.filter(user=user)
        if module in ["suivi", "budget"]:
            qs = qs.filter(module=module)
        # Trier par local_id pour que chaque utilisateur voie ses transactions dans l'ordre
        return qs.order_by("local_id")

    def perform_create(self, serializer):
        module = self.request.data.get("module", "suivi")
        # local_id sera géré automatiquement par le modèle
        serializer.save(user=self.request.user, module=module)


@api_view(["GET"])
def solde(request):
    """
    Retourne le solde (revenus - dépenses) pour l'utilisateur connecté.
    Peut filtrer par module si 'module' est passé en query param.
    """
    user = request.user
    module = request.query_params.get("module")

    transactions = Transaction.objects.filter(user=user)
    if module in ["suivi", "budget"]:
        transactions = transactions.filter(module=module)

    revenus = transactions.filter(type="revenu").aggregate(total=Sum("montant"))["total"] or 0
    depenses = transactions.filter(type="depense").aggregate(total=Sum("montant"))["total"] or 0

    return Response({
        "solde": revenus - depenses,
        "total_revenus": revenus,
        "total_depenses": depenses,
        "module": module or "suivi"
    })
