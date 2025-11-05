# backend/transactions/serializers.py
from rest_framework import serializers
from django.db.models import Q
from .models import Transaction, Libelle, Photo, Categorie

# ========== SERIALIZERS DE BASE ==========

class LibelleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Libelle
        fields = ['id', 'nom', 'date', 'montant', 'commentaire', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PhotoSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Photo
        fields = ['id', 'image', 'image_url', 'legende', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None


class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = [
            'id', 'nom', 'type_categorie', 'icone', 'couleur',
            'est_predefinite', 'est_active', 'ordre', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'est_predefinite', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Assigner l'utilisateur comme créateur
        validated_data['creee_par'] = self.context['request'].user
        return super().create(validated_data)


class CategorieDetailSerializer(serializers.ModelSerializer):
    """Version simplifiée pour l'affichage dans les transactions"""
    class Meta:
        model = Categorie
        fields = ['id', 'nom', 'icone', 'couleur', 'type_categorie']


# ========== SERIALIZERS POUR LES TRANSACTIONS ==========

class TransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer pour CRÉER une transaction avec ses libellés"""
    
    libelles = LibelleSerializer(many=True, required=True)
    categorie_id = serializers.UUIDField(write_only=True, required=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'volet', 'position', 'categorie_id',
            'statut', 'devise', 'libelles'
        ]
        read_only_fields = ['id']
    
    def validate_libelles(self, value):
        """Validation : Au moins un libellé requis"""
        if not value or len(value) == 0:
            raise serializers.ValidationError("Une transaction doit avoir au moins un libellé")
        return value
    
    def validate_categorie_id(self, value):
        """Validation : Catégorie existe et est active"""
        user = self.context['request'].user
        try:
            # Catégorie prédéfinie OU créée par l'utilisateur
            categorie = Categorie.objects.filter(
                id=value,
                est_active=True
            ).filter(
                Q(est_predefinite=True) | Q(creee_par=user)
            ).first()
            
            if not categorie:
                raise serializers.ValidationError("Catégorie invalide ou inaccessible")
            
            return value
        except Exception as e:
            raise serializers.ValidationError("Catégorie invalide ou inaccessible")
    
    def create(self, validated_data):
        # Extraire les données liées
        libelles_data = validated_data.pop('libelles')
        categorie_id = validated_data.pop('categorie_id')
        
        # Récupérer la catégorie
        try:
            categorie = Categorie.objects.get(id=categorie_id, est_active=True)
        except Categorie.DoesNotExist:
            raise serializers.ValidationError({"categorie_id": "Catégorie introuvable"})
        
        # Créer la transaction
        transaction = Transaction.objects.create(
            categorie=categorie,
            user=self.context['request'].user,  # Assigné automatiquement
            **validated_data
        )
        
        # Créer les libellés
        libelles_crees = []
        for libelle_data in libelles_data:
            libelle = Libelle.objects.create(
                transaction=transaction,
                **libelle_data
            )
            libelles_crees.append(libelle)
        
        return transaction
    
    def to_representation(self, instance):
        """Retourner la représentation complète après création"""
        return TransactionSerializer(instance, context=self.context).data


class TransactionListSerializer(serializers.ModelSerializer):
    """Serializer pour LISTER les transactions (vue simplifiée)"""
    
    categorie = CategorieDetailSerializer(read_only=True)
    montant_total = serializers.SerializerMethodField()
    nb_libelles = serializers.SerializerMethodField()
    premier_libelle = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'volet', 'position', 'categorie', 'statut',
            'devise', 'montant_total', 'nb_libelles', 'premier_libelle',
            'created_at', 'updated_at'
        ]
    
    def get_montant_total(self, obj):
        # ✅ Utiliser .all() pour convertir le RelatedManager en queryset
        return sum(libelle.montant for libelle in obj.libelles.all())
    
    def get_nb_libelles(self, obj):
        return obj.libelles.count()
    
    def get_premier_libelle(self, obj):
        """Retourne le nom du premier libellé pour l'aperçu"""
        premier = obj.libelles.first()
        return premier.nom if premier else None


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer complet pour AFFICHER/MODIFIER une transaction"""
    
    categorie = CategorieDetailSerializer(read_only=True)
    categorie_id = serializers.UUIDField(write_only=True, required=False)
    
    # ✅ Utiliser source='libelles' et many=True pour lire correctement
    libelles = LibelleSerializer(many=True, read_only=True)
    photos = PhotoSerializer(many=True, read_only=True)
    
    montant_total = serializers.SerializerMethodField()
    nb_libelles = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'user', 'volet', 'position',
            'categorie_id', 'categorie',
            'statut', 'devise',
            'libelles', 'photos',
            'montant_total', 'nb_libelles',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_montant_total(self, obj):
        # ✅ IMPORTANT : Utiliser .all() pour éviter l'erreur RelatedManager
        return sum(libelle.montant for libelle in obj.libelles.all())
    
    def get_nb_libelles(self, obj):
        return obj.libelles.count()
    
    def update(self, instance, validated_data):
        """Mise à jour d'une transaction (sans les libellés)"""
        categorie_id = validated_data.pop('categorie_id', None)
        
        if categorie_id:
            try:
                categorie = Categorie.objects.get(id=categorie_id, est_active=True)
                instance.categorie = categorie
            except Categorie.DoesNotExist:
                raise serializers.ValidationError({"categorie_id": "Catégorie introuvable"})
        
        # Mettre à jour les autres champs
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance


# ========== SERIALIZER POUR LES STATISTIQUES ==========

class StatistiquesSerializer(serializers.Serializer):
    """Serializer pour les statistiques"""
    total_revenus = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_depenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    solde = serializers.DecimalField(max_digits=12, decimal_places=2)
    nb_transactions = serializers.IntegerField()
    depenses_par_categorie = serializers.ListField()
    revenus_par_categorie = serializers.ListField()