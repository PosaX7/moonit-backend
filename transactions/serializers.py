from rest_framework import serializers
from .models import Categorie, Transaction


class CategorieSerializer(serializers.ModelSerializer):
    """Serializer pour les catégories"""
    
    nb_transactions = serializers.SerializerMethodField()
    type_categorie_display = serializers.CharField(source='get_type_categorie_display', read_only=True)
    
    class Meta:
        model = Categorie
        fields = [
            'id',
            'nom',
            'type_categorie',
            'type_categorie_display',
            'icone',
            'couleur',
            'est_predefinite',
            'est_active',
            'ordre',
            'nb_transactions',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'est_predefinite']
    
    def get_nb_transactions(self, obj):
        """Compte le nombre de transactions pour cette catégorie"""
        return obj.transactions.count()
    
    def create(self, validated_data):
        """Associe automatiquement l'utilisateur connecté lors de la création"""
        validated_data['creee_par'] = self.context['request'].user
        return super().create(validated_data)


class CategorieSimpleSerializer(serializers.ModelSerializer):
    """Version simplifiée pour les listes imbriquées"""
    
    class Meta:
        model = Categorie
        fields = ['id', 'nom', 'icone', 'couleur', 'type_categorie']


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer complet pour les transactions"""
    
    categorie_detail = CategorieSimpleSerializer(source='categorie', read_only=True)
    position_display = serializers.CharField(source='get_position_display', read_only=True)
    volet_display = serializers.CharField(source='get_volet_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'user',
            'user_username',
            'volet',
            'volet_display',
            'position',
            'position_display',
            'categorie',
            'categorie_detail',
            'libelle',
            'commentaire',
            'montant',
            'devise',
            'photo',
            'statut',
            'statut_display',
            'date',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Associe automatiquement l'utilisateur connecté lors de la création"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate_categorie(self, value):
        """Vérifie que la catégorie est active"""
        if not value.est_active:
            raise serializers.ValidationError("Cette catégorie n'est plus active.")
        return value
    
    def validate(self, data):
        """Validation croisée des champs"""
        # Vérifie que la catégorie correspond au type de transaction
        if 'categorie' in data and 'position' in data:
            if data['categorie'].type_categorie != data['position']:
                raise serializers.ValidationError({
                    'categorie': f"La catégorie doit être de type '{data['position']}'."
                })
        return data


class TransactionListSerializer(serializers.ModelSerializer):
    """Version simplifiée pour les listes de transactions"""
    
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)
    categorie_couleur = serializers.CharField(source='categorie.couleur', read_only=True)
    categorie_icone = serializers.CharField(source='categorie.icone', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'volet',
            'position',
            'categorie_nom',
            'categorie_couleur',
            'categorie_icone',
            'libelle',
            'montant',
            'devise',
            'date',
            'statut'
        ]


class StatistiquesSerializer(serializers.Serializer):
    """Serializer pour les statistiques"""
    
    total_revenus = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_depenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    solde = serializers.DecimalField(max_digits=12, decimal_places=2)
    nb_transactions = serializers.IntegerField()
    
    # Par catégorie
    depenses_par_categorie = serializers.ListField(
        child=serializers.DictField()
    )
    revenus_par_categorie = serializers.ListField(
        child=serializers.DictField()
    )