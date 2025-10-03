from django.db import models
from django.contrib.auth.models import User

class Transaction(models.Model):
    TYPE_CHOICES = [
        ("revenu", "Revenu"),
        ("depense", "Dépense"),
    ]
    
    MODULE_CHOICES = [
        ("suivi", "Suivi"),
        ("budget", "Budget"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions", null=True)
    libelle = models.CharField(max_length=255)
    categorie = models.CharField(max_length=100)
    type = models.CharField(max_length=7, choices=TYPE_CHOICES)
    module = models.CharField(max_length=6, choices=MODULE_CHOICES, default="suivi")
    montant = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.libelle} - {self.montant} - {self.module}"

    # Propriété pour formater le montant en milliers
    @property
    def montant_formate(self):
        return f"{int(self.montant):,}".replace(",", " ")

    def __str__(self):
        return f"{self.libelle} - {self.montant_formate} FCFA"
