from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Transaction(models.Model):
    TYPE_CHOICES = [
        ("revenu", "Revenu"),
        ("depense", "Dépense"),
    ]
    
    MODULE_CHOICES = [
        ("suivi", "Suivi"),
        ("budget", "Budget"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    local_id = models.PositiveIntegerField(default=0)  # ID propre à chaque utilisateur
    libelle = models.CharField(max_length=255)
    categorie = models.CharField(max_length=100)
    type = models.CharField(max_length=7, choices=TYPE_CHOICES)
    module = models.CharField(max_length=6, choices=MODULE_CHOICES, default="suivi")
    montant = models.PositiveIntegerField()
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
       # unique_together = ("user", "local_id")
        ordering = ["user", "local_id"]

    def save(self, *args, **kwargs):
        # Attribuer automatiquement un local_id si c’est une nouvelle transaction
        if not self.pk and self.user:
            last_tx = Transaction.objects.filter(user=self.user).order_by("-local_id").first()
            self.local_id = last_tx.local_id + 1 if last_tx else 0
        super().save(*args, **kwargs)

    @property
    def montant_formate(self):
        return f"{int(self.montant):,}".replace(",", " ")

    def __str__(self):
        return f"[{self.local_id}] {self.libelle} - {self.montant_formate}"


# 🔔 Signal : créer automatiquement la transaction 0
@receiver(post_save, sender=User)
def create_initial_transaction(sender, instance, created, **kwargs):
    if created:
        Transaction.objects.create(
            user=instance,
            local_id=0,
            libelle="NoTiMo",
            categorie="Conseil",
            type="revenu",
            module="suivi",
            montant=0,
        )
