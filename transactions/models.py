import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class Categorie(models.Model):
    """Catégories prédéfinies et personnalisées pour les transactions"""
    
    TYPE_CHOICES = [
        ('depense', 'Dépense'),
        ('revenu', 'Revenu'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100, verbose_name="Nom de la catégorie")
    type_categorie = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        verbose_name="Type"
    )
    icone = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Nom de l'icône (ex: health, education, travel)"
    )
    couleur = models.CharField(
        max_length=7,
        default="#3B82F6",
        help_text="Code couleur hexadécimal (ex: #3B82F6)"
    )
    est_predefinite = models.BooleanField(
        default=False,
        verbose_name="Catégorie prédéfinie",
        help_text="Les catégories prédéfinies sont proposées par défaut à tous les utilisateurs"
    )
    est_active = models.BooleanField(
        default=True,
        verbose_name="Active",
        help_text="Désactiver une catégorie la cache sans la supprimer"
    )
    creee_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='categories_creees',
        verbose_name="Créée par"
    )
    ordre = models.IntegerField(
        default=0,
        help_text="Ordre d'affichage (0 = en premier)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'transactions_categorie'
        ordering = ['ordre', 'nom']
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        unique_together = [['nom', 'type_categorie', 'creee_par']]
    
    def __str__(self):
        prefix = "🏢" if self.est_predefinite else "👤"
        return f"{prefix} {self.nom} ({self.get_type_categorie_display()})"


class Transaction(models.Model):
    """Modèle principal pour les transactions (suivi et budget)"""
    
    TYPE_CHOICES = [
        ('depense', 'Dépense'),
        ('revenu', 'Revenu'),
    ]
    
    VOLET_CHOICES = [
        ('suivi', 'Suivi'),
        ('budget', 'Budget'),
    ]
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('validee', 'Validée'),
        ('annulee', 'Annulée'),
    ]
    
    # Identifiants
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="ID unique"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name="Utilisateur"
    )
    
    # Volet et position
    volet = models.CharField(
        max_length=10,
        choices=VOLET_CHOICES,
        default='suivi',
        verbose_name="Volet",
        help_text="S'agit-il d'un suivi réel ou d'un budget prévisionnel ?"
    )
    position = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        verbose_name="Position",
        help_text="S'agit-il d'une dépense ou d'un revenu ?"
    )
    
    # Catégorie
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name="Catégorie"
    )
    
    # Informations de la transaction
    libelle = models.CharField(
        max_length=200,
        verbose_name="Libellé",
        help_text="Description courte de la transaction"
    )
    commentaire = models.TextField(
        blank=True,
        null=True,
        verbose_name="Commentaire",
        help_text="Notes ou détails supplémentaires"
    )
    
    # Montant
    montant = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Montant"
    )
    devise = models.CharField(
        max_length=3,
        default='XAF',
        verbose_name="Devise"
    )
    
    # Photo/Reçu
    photo = models.ImageField(
        upload_to='transactions/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Photo/Reçu",
        help_text="Photo de la transaction ou du reçu"
    )
    
    # Statut et dates
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='validee',
        verbose_name="Statut"
    )
    date = models.DateTimeField(
        verbose_name="Date de la transaction"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créée le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifiée le")
    
    class Meta:
        db_table = 'transactions_transaction'
        ordering = ['-date']
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'volet', 'position']),
            models.Index(fields=['categorie', 'date']),
        ]
    
    def __str__(self):
        symbole = "💰" if self.position == 'revenu' else "💸"
        return f"{symbole} {self.libelle} - {self.montant} {self.devise}"
    
    @property
    def est_budget(self):
        """Vérifie si c'est une entrée de budget"""
        return self.volet == 'budget'
    
    @property
    def est_suivi(self):
        """Vérifie si c'est une entrée de suivi réel"""
        return self.volet == 'suivi'