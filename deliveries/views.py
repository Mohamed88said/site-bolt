from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from .models import Delivery, DeliveryRequest, DeliveryRating
from .forms import DeliveryRequestForm, DeliveryRatingForm
from geolocation.models import UserLocation, LocationPoint
from notifications.models import Notification
from django.utils import timezone

class DeliveryListView(LoginRequiredMixin, ListView):
    model = Delivery
    template_name = 'deliveries/list.html'
    context_object_name = 'deliveries'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Delivery.objects.select_related('order', 'delivery_person', 'location_point')
        
        if self.request.user.user_type == 'delivery':
            # Livreur voit ses livraisons + celles disponibles
            queryset = queryset.filter(
                Q(delivery_person=self.request.user) |
                Q(status='pending', delivery_person__isnull=True)
            )
        elif self.request.user.user_type == 'buyer':
            # Acheteur voit ses livraisons
            queryset = queryset.filter(order__user=self.request.user)
        elif self.request.user.user_type == 'seller':
            # Vendeur voit les livraisons de ses produits
            queryset = queryset.filter(order__items__product__seller=self.request.user).distinct()
        
        return queryset.order_by('-created_at')

class DeliveryDetailView(LoginRequiredMixin, DetailView):
    model = Delivery
    template_name = 'deliveries/detail.html'
    context_object_name = 'delivery'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        delivery = self.get_object()
        
        # Ajouter les informations de distance si possible
        if delivery.location_point:
            seller = delivery.order.items.first().product.seller if delivery.order.items.exists() else None
            if seller and hasattr(seller, 'seller_profile') and seller.seller_profile.location_point:
                distance = seller.seller_profile.location_point.calculate_distance_to(delivery.location_point)
                context['distance_km'] = round(distance, 2) if distance else None
        
        return context

@login_required
def available_deliveries(request):
    """Livraisons disponibles pour les livreurs"""
    if request.user.user_type != 'delivery':
        messages.error(request, 'Vous devez être livreur pour accéder à cette page.')
        return redirect('deliveries:list')
    
    deliveries = Delivery.objects.filter(
        status='pending',
        delivery_person__isnull=True
    ).select_related('order', 'location_point')
    
    return render(request, 'deliveries/available.html', {'deliveries': deliveries})

@login_required
def delivery_map(request, delivery_id):
    """Carte pour choisir un livreur"""
    delivery = get_object_or_404(Delivery, id=delivery_id)
    
    # Vérifier les permissions
    if request.user.user_type == 'seller':
        # Vérifier que c'est le vendeur du produit
        if not delivery.order.items.filter(product__seller=request.user).exists():
            messages.error(request, "Vous n'avez pas accès à cette livraison.")
            return redirect('deliveries:list')
    elif request.user.user_type == 'buyer':
        # Vérifier que c'est l'acheteur
        if delivery.order.user != request.user:
            messages.error(request, "Vous n'avez pas accès à cette livraison.")
            return redirect('deliveries:list')
    else:
        messages.error(request, "Accès non autorisé.")
        return redirect('deliveries:list')
    
    # Trouver les livreurs disponibles
    available_delivery_persons = []
    if delivery.location_point:
        # Tous les livreurs avec profil vérifié
        from accounts.models import User
        delivery_users = User.objects.filter(
            user_type='delivery',
            delivery_profile__verification_status='approved',
            delivery_profile__is_available=True
        ).select_related('delivery_profile')
        
        for delivery_user in delivery_users:
            # Calculer la distance si possible
            distance = None
            if hasattr(delivery_user, 'delivery_profile') and delivery_user.delivery_profile.location_point:
                distance = delivery.location_point.calculate_distance_to(delivery_user.delivery_profile.location_point)
            
            available_delivery_persons.append({
                'user': delivery_user,
                'distance': round(distance, 2) if distance else None,
                'existing_request': DeliveryRequest.objects.filter(
                    delivery=delivery, 
                    delivery_person=delivery_user
                ).first()
            })
    
    context = {
        'delivery': delivery,
        'available_delivery_persons': available_delivery_persons,
        'delivery_location': delivery.location_point,
    }
    
    return render(request, 'deliveries/delivery_map.html', context)

@login_required
def request_delivery(request, delivery_id):
    """Faire une demande de livraison"""
    if request.user.user_type != 'delivery':
        messages.error(request, 'Vous devez être livreur.')
        return redirect('deliveries:list')
    
    delivery = get_object_or_404(Delivery, id=delivery_id, status='pending')
    
    # Vérifier si une demande existe déjà
    existing_request = DeliveryRequest.objects.filter(
        delivery=delivery,
        delivery_person=request.user
    ).first()
    
    if existing_request:
        messages.info(request, 'Vous avez déjà fait une demande pour cette livraison.')
        return redirect('deliveries:detail', pk=delivery_id)
    
    if request.method == 'POST':
        form = DeliveryRequestForm(request.POST)
        if form.is_valid():
            delivery_request = form.save(commit=False)
            delivery_request.delivery = delivery
            delivery_request.delivery_person = request.user
            delivery_request.save()
            
            # Notifier le vendeur
            seller = delivery.order.items.first().product.seller
            Notification.objects.create(
                user=seller,
                title='Nouvelle demande de livraison',
                message=f'Le livreur {request.user.username} propose de livrer votre commande pour {delivery_request.proposed_cost} GNF.',
                notification_type='delivery_request',
                url=reverse('deliveries:delivery_map', kwargs={'delivery_id': delivery.id})
            )
            
            messages.success(request, 'Votre demande a été envoyée au vendeur.')
            return redirect('deliveries:detail', pk=delivery_id)
    else:
        # Calculer un coût proposé basé sur la distance
        proposed_cost = delivery.calculate_delivery_cost()
        form = DeliveryRequestForm(initial={'proposed_cost': proposed_cost})
    
    return render(request, 'deliveries/request_form.html', {
        'form': form,
        'delivery': delivery
    })

@login_required
def accept_delivery_request(request, request_id):
    """Accepter une demande de livraison"""
    delivery_request = get_object_or_404(DeliveryRequest, id=request_id)
    delivery = delivery_request.delivery
    
    # Vérifier que c'est le vendeur
    if not delivery.order.items.filter(product__seller=request.user).exists():
        return JsonResponse({'success': False, 'error': 'Non autorisé'})
    
    if delivery.status != 'pending':
        return JsonResponse({'success': False, 'error': 'Livraison déjà assignée'})
    
    # Assigner le livreur
    delivery.delivery_person = delivery_request.delivery_person
    delivery.delivery_cost = delivery_request.proposed_cost
    delivery.status = 'assigned'
    delivery.save()
    
    # Marquer la demande comme acceptée
    delivery_request.is_accepted = True
    delivery_request.save()
    
    # Supprimer les autres demandes
    DeliveryRequest.objects.filter(delivery=delivery).exclude(id=request_id).delete()
    
    # Notifier le livreur
    Notification.objects.create(
        user=delivery_request.delivery_person,
        title='Livraison assignée',
        message=f'Votre demande pour la livraison #{delivery.tracking_number} a été acceptée.',
        notification_type='delivery_accepted',
        url=reverse('deliveries:detail', kwargs={'pk': delivery.id})
    )
    
    return JsonResponse({'success': True})

@login_required
def start_delivery(request, delivery_id):
    """Démarrer une livraison"""
    delivery = get_object_or_404(Delivery, id=delivery_id, delivery_person=request.user)
    
    if delivery.status == 'assigned':
        delivery.status = 'in_progress'
        delivery.save()
        messages.success(request, 'Livraison démarrée.')
    else:
        messages.error(request, 'Cette livraison ne peut pas être démarrée.')
    
    return redirect('deliveries:detail', pk=delivery_id)

@login_required
def complete_delivery(request, delivery_id):
    """Terminer une livraison"""
    delivery = get_object_or_404(Delivery, id=delivery_id, delivery_person=request.user)
    
    if delivery.status == 'in_progress':
        delivery.status = 'completed'
        delivery.actual_delivery_time = timezone.now()
        delivery.save()
        
        # Mettre à jour la commande
        delivery.order.status = 'delivered'
        delivery.order.save()
        
        messages.success(request, 'Livraison terminée avec succès.')
    else:
        messages.error(request, 'Cette livraison ne peut pas être terminée.')
    
    return redirect('deliveries:detail', pk=delivery_id)

@login_required
def rate_delivery(request, delivery_id):
    """Noter une livraison"""
    delivery = get_object_or_404(Delivery, id=delivery_id, order__user=request.user)
    
    if delivery.status != 'completed':
        messages.error(request, 'Vous ne pouvez noter que les livraisons terminées.')
        return redirect('deliveries:detail', pk=delivery_id)
    
    if request.method == 'POST':
        form = DeliveryRatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.delivery = delivery
            rating.created_by = request.user
            rating.save()
            
            messages.success(request, 'Votre évaluation a été enregistrée.')
            return redirect('deliveries:detail', pk=delivery_id)
    else:
        form = DeliveryRatingForm()
    
    return render(request, 'deliveries/rate_form.html', {
        'form': form,
        'delivery': delivery
    })