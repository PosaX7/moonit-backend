from rest_framework import serializers
from .models import Categorie, Transaction, Libelle, Photo


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


class LibelleSerializer(serializers.ModelSerializer):
    """Serializer pour les libellés"""
    
    class Meta:
        model = Libelle
        fields = [
            'id',
            'nom',
            'date',
            'montant',
            'commentaire',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PhotoSerializer(serializers.ModelSerializer):
    """Serializer pour les photos"""
    
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Photo
        fields = [
            'id',
            'image',
            'image_url',
            'legende',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_image_url(self, obj):
        """Retourne l'URL complète de l'image"""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer complet pour les transactions avec libellés et photos"""
    
    categorie_detail = CategorieSimpleSerializer(source='categorie', read_only=True)
    position_display = serializers.CharField(source='get_position_display', read_only=True)
    volet_display = serializers.CharField(source='get_volet_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    # Relations imbriquées
    libelles = LibelleSerializer(many=True, read_only=False)
    photos = PhotoSerializer(many=True, read_only=True)
    
    # Champs calculés
    montant_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    nb_libelles = serializers.SerializerMethodField()
    
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
            'statut',
            'statut_display',
            'devise',
            'libelles',
            'photos',
            'montant_total',
            'nb_libelles',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'montant_total']
    
    def get_nb_libelles(self, obj):
        """Compte le nombre de libellés"""
        return obj.libelles.count()
    
    def create(self, validated_data):
        """Créer une transaction avec ses libellés"""
        libelles_data = validated_data.pop('libelles', [])
        
        # Créer la transaction
        validated_data['user'] = self.context['request'].user
        transaction = Transaction.objects.create(**validated_data)
        
        # Créer les libellés
        for libelle_data in libelles_data:
            Libelle.objects.create(transaction=transaction, **libelle_data)
        
        return transaction
    
    def update(self, instance, validated_data):
        """Mettre à jour une transaction et ses libellés"""
        libelles_data = validated_data.pop('libelles', None)
        
        # Mettre à jour les champs de la transaction
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Si des libellés sont fournis, remplacer les anciens
        if libelles_data is not None:
            # Supprimer les anciens libellés
            instance.libelles.all().delete()
            
            # Créer les nouveaux libellés
            for libelle_data in libelles_data:
                Libelle.objects.create(transaction=instance, **libelle_data)
        
        return instance
    
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
        
        # Vérifie qu'il y a au moins un libellé
        if 'libelles' in data and len(data['libelles']) == 0:
            raise serializers.ValidationError({
                'libelles': "Une transaction doit avoir au moins un libellé."
            })
        
        return data


class TransactionListSerializer(serializers.ModelSerializer):
    """Version simplifiée pour les listes de transactions"""
    
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)
    categorie_couleur = serializers.CharField(source='categorie.couleur', read_only=True)
    categorie_icone = serializers.CharField(source='categorie.icone', read_only=True)
    montant_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    nb_libelles = serializers.SerializerMethodField()
    date_premier_libelle = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id',
            'volet',
            'position',
            'categorie_nom',
            'categorie_couleur',
            'categorie_icone',
            'montant_total',
            'nb_libelles',
            'devise',
            'date_premier_libelle',
            'statut',
            'created_at'
        ]
    
    def get_nb_libelles(self, obj):
        """Compte le nombre de libellés"""
        return obj.libelles.count()
    
    def get_date_premier_libelle(self, obj):
        """Retourne la date du premier libellé"""
        premier = obj.libelles.first()
        return premier.date if premier else obj.created_at


class TransactionCreateSerializer(serializers.Serializer):
    """Serializer simplifié pour la création depuis le frontend"""
    
    position = serializers.ChoiceField(choices=['depense', 'revenu'])
    categorie_id = serializers.UUIDField()
    volet = serializers.ChoiceField(choices=['suivi', 'budget'], default='suivi')
    libelles = serializers.ListField(
        child=serializers.DictField(),
        min_length=1
    )
    
    def validate_libelles(self, value):
        """Valide chaque libellé"""
        for libelle in value:
            if 'nom' not in libelle or not libelle['nom']:
                raise serializers.ValidationError("Chaque libellé doit avoir un nom.")
            if 'montant' not in libelle or float(libelle['montant']) <= 0:
                raise serializers.ValidationError("Chaque libellé doit avoir un montant positif.")
            if 'date' not in libelle:
                raise serializers.ValidationError("Chaque libellé doit avoir une date.")
        return value
    
    def create(self, validated_data):
        """Créer une transaction avec ses libellés"""
        from django.utils import timezone
        
        categorie_id = validated_data['categorie_id']
        libelles_data = validated_data['libelles']
        
        # Récupérer la catégorie
        try:
            categorie = Categorie.objects.get(id=categorie_id)
        except Categorie.DoesNotExist:
            raise serializers.ValidationError({'categorie_id': 'Catégorie introuvable.'})
        
        # Créer la transaction
        transaction = Transaction.objects.create(
            user=self.context['request'].user,
            volet=validated_data.get('volet', 'suivi'),
            position=validated_data['position'],
            categorie=categorie,
            statut='validee'
        )
        
        # Créer les libellés
        for libelle_data in libelles_data:
            Libelle.objects.create(
                transaction=transaction,
                nom=libelle_data['nom'],
                date=libelle_data['date'],
                montant=libelle_data['montant'],
                commentaire=libelle_data.get('commentaire', '')
            )
        
        return transaction


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