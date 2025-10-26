from django.contrib import admin
from django.utils.html import format_html
from .models import Categorie, Transaction, Libelle, Photo


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


class LibelleInline(admin.TabularInline):
    """Inline pour afficher les libellés dans la transaction"""
    model = Libelle
    extra = 1
    fields = ['nom', 'date', 'montant', 'commentaire']


class PhotoInline(admin.TabularInline):
    """Inline pour afficher les photos dans la transaction"""
    model = Photo
    extra = 0
    fields = ['image', 'legende', 'image_preview']
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        """Prévisualisation de l'image"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:100px;max-height:100px;border-radius:4px;" />',
                obj.image.url
            )
        return "—"
    image_preview.short_description = 'Aperçu'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'categorie_display',
        'montant_total_display',
        'nb_libelles_display',
        'position',
        'volet',
        'user',
        'created_at',
        'statut'
    ]
    list_filter = [
        'volet',
        'position',
        'statut',
        'categorie',
        'created_at',
        'user'
    ]
    search_fields = ['id', 'categorie__nom', 'libelles__nom']
    readonly_fields = ['id', 'created_at', 'updated_at', 'montant_total']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    inlines = [LibelleInline, PhotoInline]
    
    fieldsets = (
        ('Type de transaction', {
            'fields': ('volet', 'position', 'categorie')
        }),
        ('Propriétaire', {
            'fields': ('user', 'statut', 'devise')
        }),
        ('Résumé', {
            'fields': ('montant_total',),
            'description': 'Le montant total est calculé automatiquement à partir des libellés'
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def montant_total_display(self, obj):
        """Affiche le montant total avec couleur"""
        montant = obj.montant_total
        if obj.position == 'revenu':
            color = '#10B981'
            symbole = '+'
        else:
            color = '#EF4444'
            symbole = '-'
        
        return format_html(
            '<span style="color:{};font-weight:bold;">{}{} {}</span>',
            color,
            symbole,
            montant,
            obj.devise
        )
    montant_total_display.short_description = 'Montant Total'
    
    def nb_libelles_display(self, obj):
        """Affiche le nombre de libellés"""
        count = obj.libelles.count()
        return format_html(
            '<span style="background:#e2e8f0;padding:4px 8px;border-radius:4px;font-weight:600;">{} libellé{}</span>',
            count,
            's' if count > 1 else ''
        )
    nb_libelles_display.short_description = 'Libellés'
    
    def categorie_display(self, obj):
        """Affiche la catégorie avec sa couleur"""
        return format_html(
            '<span style="display:inline-block;padding:4px 8px;background-color:{};color:white;border-radius:4px;font-size:11px;">{}</span>',
            obj.categorie.couleur,
            obj.categorie.nom
        )
    categorie_display.short_description = 'Catégorie'
    
    actions = ['valider_transactions', 'annuler_transactions']
    
    def valider_transactions(self, request, queryset):
        updated = queryset.update(statut='validee')
        self.message_user(request, f"{updated} transaction(s) validée(s).")
    valider_transactions.short_description = "Valider les transactions sélectionnées"
    
    def annuler_transactions(self, request, queryset):
        updated = queryset.update(statut='annulee')
        self.message_user(request, f"{updated} transaction(s) annulée(s).")
    annuler_transactions.short_description = "Annuler les transactions sélectionnées"


@admin.register(Libelle)
class LibelleAdmin(admin.ModelAdmin):
    list_display = ['nom', 'transaction_info', 'montant', 'date', 'created_at']
    list_filter = ['date', 'transaction__position', 'transaction__categorie']
    search_fields = ['nom', 'commentaire', 'transaction__id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Transaction', {
            'fields': ('transaction',)
        }),
        ('Détails', {
            'fields': ('nom', 'date', 'montant', 'commentaire')
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def transaction_info(self, obj):
        """Affiche des infos sur la transaction parente"""
        return format_html(
            '<span style="color:{};">{}</span>',
            obj.transaction.categorie.couleur,
            obj.transaction.categorie.nom
        )
    transaction_info.short_description = 'Transaction'


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['image_preview', 'transaction_info', 'legende', 'created_at']
    list_filter = ['created_at', 'transaction__position']
    search_fields = ['legende', 'transaction__id']
    readonly_fields = ['id', 'created_at', 'image_preview_large']
    
    fieldsets = (
        ('Transaction', {
            'fields': ('transaction',)
        }),
        ('Photo', {
            'fields': ('image', 'image_preview_large', 'legende')
        }),
        ('Métadonnées', {
            'fields': ('id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        """Petite prévisualisation"""
        if obj.image:
            return format_html(
                '<img src="{}" style="width:60px;height:60px;object-fit:cover;border-radius:4px;" />',
                obj.image.url
            )
        return "—"
    image_preview.short_description = 'Aperçu'
    
    def image_preview_large(self, obj):
        """Grande prévisualisation"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:400px;max-height:400px;border-radius:8px;" />',
                obj.image.url
            )
        return "Aucune image"
    image_preview_large.short_description = 'Image'
    
    def transaction_info(self, obj):
        """Affiche des infos sur la transaction parente"""
        return format_html(
            '<span style="color:{};">{}</span>',
            obj.transaction.categorie.couleur,
            obj.transaction.categorie.nom
        )
    transaction_info.short_description = 'Transaction'