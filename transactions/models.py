from django.db import models

class Transaction(models.Model):
    libelle = models.CharField(max_length=255)
    montant = models.FloatField()
    categorie = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=[('revenu', 'Revenu'), ('depense', 'Dépense')])
    date = models.DateTimeField(auto_now_add=True)

    # Propriété pour formater le montant en milliers
    @property
    def montant_formate(self):
        return f"{int(self.montant):,}".replace(",", " ")

    def __str__(self):
        return f"{self.libelle} - {self.montant_formate} FCFA"
