from django.contrib import admin
from django.utils.html import format_html
from .models import Categorie, Transaction


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = [
        'nom',
        'type_categorie',
        'couleur_preview',
        'est_predefinite',
        'est_active',
        'ordre',
        'nb_transactions'
    ]
    list_filter = ['type_categorie', 'est_predefinite', 'est_active']
    search_fields = ['nom']
    ordering = ['ordre', 'nom']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'type_categorie', 'icone', 'couleur')
        }),
        ('Configuration', {
            'fields': ('est_predefinite', 'est_active', 'ordre', 'creee_par')
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def couleur_preview(self, obj):
        """Affiche un aperçu de la couleur"""
        return format_html(
            '<div style="width:30px;height:30px;background-color:{};border:1px solid #ccc;border-radius:4px;"></div>',
            obj.couleur
        )
    couleur_preview.short_description = 'Couleur'
    
    def nb_transactions(self, obj):
        """Compte le nombre de transactions associées"""
        count = obj.transactions.count()
        return format_html('<strong>{}</strong>', count)
    nb_transactions.short_description = 'Transactions'
    
    actions = ['activer_categories', 'desactiver_categories']
    
    def activer_categories(self, request, queryset):
        updated = queryset.update(est_active=True)
        self.message_user(request, f"{updated} catégorie(s) activée(s).")
    activer_categories.short_description = "Activer les catégories sélectionnées"
    
    def desactiver_categories(self, request, queryset):
        updated = queryset.update(est_active=False)
        self.message_user(request, f"{updated} catégorie(s) désactivée(s).")
    desactiver_categories.short_description = "Désactiver les catégories sélectionnées"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'libelle',
        'montant_display',
        'position',
        'volet',
        'categorie_display',
        'user',
        'date',
        'statut',
        'photo_preview'
    ]
    list_filter = [
        'volet',
        'position',
        'statut',
        'categorie',
        'date',
        'user'
    ]
    search_fields = ['libelle', 'commentaire', 'id']
    readonly_fields = ['id', 'created_at', 'updated_at', 'photo_preview_large']
    date_hierarchy = 'date'
    ordering = ['-date']
    
    fieldsets = (
        ('Type de transaction', {
            'fields': ('volet', 'position', 'categorie')
        }),
        ('Détails', {
            'fields': ('libelle', 'commentaire')
        }),
        ('Montant', {
            'fields': ('montant', 'devise')
        }),
        ('Justificatif', {
            'fields': ('photo', 'photo_preview_large')
        }),
        ('Propriétaire', {
            'fields': ('user', 'statut', 'date')
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def montant_display(self, obj):
        """Affiche le montant avec couleur selon le type"""
        if obj.position == 'revenu':
            color = '#10B981'  # vert
            symbole = '+'
        else:
            color = '#EF4444'  # rouge
            symbole = '-'
        
        return format_html(
            '<span style="color:{};font-weight:bold;">{}{} {}</span>',
            color,
            symbole,
            obj.montant,
            obj.devise
        )
    montant_display.short_description = 'Montant'
    montant_display.admin_order_field = 'montant'
    
    def categorie_display(self, obj):
        """Affiche la catégorie avec sa couleur"""
        return format_html(
            '<span style="display:inline-block;padding:4px 8px;background-color:{};color:white;border-radius:4px;font-size:11px;">{}</span>',
            obj.categorie.couleur,
            obj.categorie.nom
        )
    categorie_display.short_description = 'Catégorie'
    
    def photo_preview(self, obj):
        """Petite prévisualisation de la photo dans la liste"""
        if obj.photo:
            return format_html(
                '<img src="{}" style="width:40px;height:40px;object-fit:cover;border-radius:4px;" />',
                obj.photo.url
            )
        return "—"
    photo_preview.short_description = 'Photo'
    
    def photo_preview_large(self, obj):
        """Grande prévisualisation de la photo dans le détail"""
        if obj.photo:
            return format_html(
                '<img src="{}" style="max-width:400px;max-height:400px;border-radius:8px;" />',
                obj.photo.url
            )
        return "Aucune photo"
    photo_preview_large.short_description = 'Aperçu de la photo'
    
    actions = ['valider_transactions', 'annuler_transactions']
    
    def valider_transactions(self, request, queryset):
        updated = queryset.update(statut='validee')
        self.message_user(request, f"{updated} transaction(s) validée(s).")
    valider_transactions.short_description = "Valider les transactions sélectionnées"
    
    def annuler_transactions(self, request, queryset):
        updated = queryset.update(statut='annulee')
        self.message_user(request, f"{updated} transaction(s) annulée(s).")
    annuler_transactions.short_description = "Annuler les transactions sélectionnées"