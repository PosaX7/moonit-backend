from django.contrib.auth.models import User
from django.db import models

class Compte(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comptes")
    nom = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.nom} ({self.user.username})"
