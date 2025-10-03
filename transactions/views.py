from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum
from .models import Transaction
from .serializers import TransactionSerializer

# ---------------------------
# TransactionViewSet
# ---------------------------
class TransactionViewSet(viewsets.ModelViewSet):
    """
    Gère la création, la lecture, la mise à jour et la suppression
    des transactions de l'utilisateur connecté uniquement.
    Permet de distinguer les modules : 'suivi' ou 'budget'.
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retourne uniquement les transactions de l'utilisateur connecté,
        triées par date décroissante, et filtrées par module si précisé.
        """
        user = self.request.user
        module = self.request.query_params.get("module")  # 'suivi' ou 'budget'
        qs = Transaction.objects.filter(user=user)
        if module in ["suivi", "budget"]:
            qs = qs.filter(module=module)
        return qs.order_by("-date")

    def perform_create(self, serializer):
        """
        Crée une transaction et l'associe automatiquement à l'utilisateur connecté.
        Le module par défaut est 'suivi', mais peut être passé dans la requête.
        """
        module = self.request.data.get("module", "suivi")
        serializer.save(user=self.request.user, module=module)


# ---------------------------
# Solde API
# ---------------------------
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
