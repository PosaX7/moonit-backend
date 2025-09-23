from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum
from .models import Transaction
from .serializers import TransactionSerializer

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all().order_by("-id")
    serializer_class = TransactionSerializer

@api_view(["GET"])
def solde(request):
    revenus = Transaction.objects.filter(type="revenu").aggregate(total=Sum("montant"))["total"] or 0
    depenses = Transaction.objects.filter(type="depense").aggregate(total=Sum("montant"))["total"] or 0
    return Response({"solde": revenus - depenses})
