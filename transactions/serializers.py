from rest_framework import serializers
from .models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    montant_formate = serializers.SerializerMethodField(read_only=True)
    date_formatee = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id',
            'libelle',
            'categorie',
            'type',
            'date',
            'montant',
            'montant_formate',
            'date_formatee',
        ]

    def get_montant_formate(self, obj):
        return f"{int(obj.montant):,}".replace(",", " ")

    def get_date_formatee(self, obj):
        # Exemple : "22/09/2025 14:30"
        return obj.date.strftime("%d/%m/%Y %H:%M")
