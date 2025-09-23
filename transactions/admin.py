from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "libelle", "montant", "categorie", "type", "date")
    list_filter = ("type", "categorie")
    search_fields = ("libelle",)
    ordering = ("-id",)