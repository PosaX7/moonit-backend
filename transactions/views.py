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
    + Filtres avancés : description, type, date, mois.
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Transaction.objects.filter(user=user)

        # --- Filtrage par module (déjà présent) ---
        module = self.request.query_params.get("module")
        if module in ["suivi", "budget"]:
            qs = qs.filter(module=module)

        # --- 🔍 Nouveaux filtres personnalisés ---
        description = self.request.query_params.get("description")  # libellé
        type_ = self.request.query_params.get("type")               # revenu / depense
        date = self.request.query_params.get("date")                # format YYYY-MM-DD
        month = self.request.query_params.get("month")              # format YYYY-MM

        if description:
            qs = qs.filter(description__icontains=description)
        if type_:
            qs = qs.filter(type__iexact=type_)
        if date:
            qs = qs.filter(date__date=date)
        if month:
            try:
                year, month_num = month.split("-")
                qs = qs.filter(date__year=year, date__month=month_num)
            except ValueError:
                pass  # Ignore si mauvais format

        # Trier par local_id pour garder l’ordre d’insertion
        return qs.order_by("local_id")

    def perform_create(self, serializer):
        module = self.request.data.get("module", "suivi")
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
