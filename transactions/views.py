from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, timedelta
from .models import Categorie, Transaction
from .serializers import (
    CategorieSerializer,
    TransactionSerializer,
    TransactionListSerializer,
    StatistiquesSerializer
)


class CategorieViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les catégories
    
    list: Liste toutes les catégories (prédéfinies + personnalisées de l'utilisateur)
    create: Créer une catégorie personnalisée
    retrieve: Détails d'une catégorie
    update/partial_update: Modifier une catégorie personnalisée
    destroy: Supprimer une catégorie personnalisée (si pas de transactions associées)
    """
    
    serializer_class = CategorieSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type_categorie', 'est_active']
    search_fields = ['nom']
    ordering_fields = ['nom', 'ordre', 'created_at']
    ordering = ['ordre', 'nom']
    
    def get_queryset(self):
        """Retourne les catégories prédéfinies + celles créées par l'utilisateur"""
        return Categorie.objects.filter(
            Q(est_predefinite=True) | Q(creee_par=self.request.user)
        ).filter(est_active=True)
    
    @action(detail=False, methods=['get'])
    def predefinies(self, request):
        """Liste uniquement les catégories prédéfinies"""
        categories = Categorie.objects.filter(
            est_predefinite=True,
            est_active=True
        )
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def personnalisees(self, request):
        """Liste uniquement les catégories personnalisées de l'utilisateur"""
        categories = Categorie.objects.filter(
            creee_par=request.user,
            est_active=True
        )
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Empêche la suppression si des transactions sont associées"""
        instance = self.get_object()
        
        # Vérifie que c'est une catégorie personnalisée
        if instance.est_predefinite:
            return Response(
                {"error": "Impossible de supprimer une catégorie prédéfinie."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Vérifie qu'il n'y a pas de transactions associées
        if instance.transactions.exists():
            return Response(
                {"error": "Impossible de supprimer une catégorie avec des transactions associées."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)


class TransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer les transactions
    
    list: Liste toutes les transactions de l'utilisateur
    create: Créer une transaction
    retrieve: Détails d'une transaction
    update/partial_update: Modifier une transaction
    destroy: Supprimer une transaction
    
    Actions supplémentaires:
    - statistiques: Obtenir des stats sur les transactions
    - par_mois: Filtrer les transactions d'un mois spécifique
    - budget: Filtrer uniquement les budgets
    - suivi: Filtrer uniquement le suivi réel
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['volet', 'position', 'statut', 'categorie']
    search_fields = ['libelle', 'commentaire']
    ordering_fields = ['date', 'montant', 'created_at']
    ordering = ['-date']
    
    def get_queryset(self):
        """Retourne uniquement les transactions de l'utilisateur connecté"""
        return Transaction.objects.filter(user=self.request.user).select_related('categorie')
    
    def get_serializer_class(self):
        """Utilise un serializer simplifié pour les listes"""
        if self.action == 'list':
            return TransactionListSerializer
        return TransactionSerializer
    
    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """
        Calcule les statistiques des transactions
        Query params:
        - volet: 'suivi' ou 'budget' (optionnel)
        - date_debut: YYYY-MM-DD (optionnel)
        - date_fin: YYYY-MM-DD (optionnel)
        """
        queryset = self.get_queryset()
        
        # Filtres optionnels
        volet = request.query_params.get('volet')
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        
        if volet:
            queryset = queryset.filter(volet=volet)
        if date_debut:
            queryset = queryset.filter(date__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date__lte=date_fin)
        
        # Calculs
        revenus = queryset.filter(position='revenu', statut='validee').aggregate(
            total=Sum('montant')
        )['total'] or 0
        
        depenses = queryset.filter(position='depense', statut='validee').aggregate(
            total=Sum('montant')
        )['total'] or 0
        
        solde = revenus - depenses
        nb_transactions = queryset.count()
        
        # Dépenses par catégorie
        depenses_cat = queryset.filter(
            position='depense',
            statut='validee'
        ).values(
            'categorie__nom',
            'categorie__couleur',
            'categorie__icone'
        ).annotate(
            total=Sum('montant'),
            nombre=Count('id')
        ).order_by('-total')
        
        # Revenus par catégorie
        revenus_cat = queryset.filter(
            position='revenu',
            statut='validee'
        ).values(
            'categorie__nom',
            'categorie__couleur',
            'categorie__icone'
        ).annotate(
            total=Sum('montant'),
            nombre=Count('id')
        ).order_by('-total')
        
        data = {
            'total_revenus': revenus,
            'total_depenses': depenses,
            'solde': solde,
            'nb_transactions': nb_transactions,
            'depenses_par_categorie': list(depenses_cat),
            'revenus_par_categorie': list(revenus_cat)
        }
        
        serializer = StatistiquesSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def par_mois(self, request):
        """
        Filtre les transactions d'un mois spécifique
        Query params:
        - annee: YYYY (requis)
        - mois: MM (requis)
        - volet: 'suivi' ou 'budget' (optionnel)
        """
        annee = request.query_params.get('annee')
        mois = request.query_params.get('mois')
        
        if not annee or not mois:
            return Response(
                {"error": "Les paramètres 'annee' et 'mois' sont requis."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            queryset = self.get_queryset().filter(
                date__year=int(annee),
                date__month=int(mois)
            )
            
            volet = request.query_params.get('volet')
            if volet:
                queryset = queryset.filter(volet=volet)
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        
        except ValueError:
            return Response(
                {"error": "Format de date invalide."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def budget(self, request):
        """Retourne uniquement les transactions de type budget"""
        queryset = self.get_queryset().filter(volet='budget')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def suivi(self, request):
        """Retourne uniquement les transactions de type suivi"""
        queryset = self.get_queryset().filter(volet='suivi')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recentes(self, request):
        """Retourne les 10 dernières transactions"""
        queryset = self.get_queryset()[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)