from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Delivery, DeliveryRequest, DeliveryRating, DeliveryPerson
from .forms import DeliveryRequestForm, DeliveryRatingForm
from accounts.models import User
from notifications.models import Notification

class DeliveryListView(LoginRequiredMixin, ListView):
    model = Delivery
    template_name = 'deliveries/list.html'
    context_object_name = 'deliveries'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Delivery.objects.select_related('order', 'delivery_person', 'location_point')
        
        if self.request.user.user_type == 'delivery':
            # Livreur voit ses livraisons
            queryset = queryset.filter(delivery_person=self.request.user)
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
        
        # Calculer la distance si possible
        distance = delivery.calculate_distance_to_seller()
        if distance:
            context['distance_km'] = round(distance, 2)
            context['estimated_cost'] = delivery.calculate_delivery_cost()
        
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
    ).select_related('order', 'location_point').prefetch_related('requests')
    
    return render(request, 'deliveries/available.html', {'deliveries': deliveries})

@login_required
def delivery_map(request, delivery_id):
    """Carte pour choisir un livreur (vendeur)"""
    delivery = get_object_or_404(Delivery, id=delivery_id)
    
    # Vérifier les permissions
    if request.user.user_type == 'seller':
        if not delivery.order.items.filter(product__seller=request.user).exists():
            messages.error(request, "Vous n'avez pas accès à cette livraison.")
            return redirect('deliveries:list')
    elif request.user.user_type == 'buyer':
        if delivery.order.user != request.user:
            messages.error(request, "Vous n'avez pas accès à cette livraison.")
            return redirect('deliveries:list')
    else:
        messages.error(request, "Accès non autorisé.")
        return redirect('deliveries:list')
    
    # Trouver les livreurs disponibles
    delivery_persons = User.objects.filter(
        user_type='delivery',
        delivery_profile__verification_status='approved',
        delivery_profile__is_available=True
    ).select_related('delivery_profile')
    
    # Enrichir avec les informations de distance et demandes existantes
    delivery_persons_data = []
    for person in delivery_persons:
        # Calculer la distance si possible
        distance = None
        if delivery.location_point and hasattr(person, 'delivery_person_profile') and person.delivery_person_profile.location_point:
            distance = delivery.location_point.calculate_distance_to(person.delivery_person_profile.location_point)
        
        # Vérifier s'il y a une demande existante
        existing_request = DeliveryRequest.objects.filter(
            delivery=delivery,
            delivery_person=person
        ).first()
        
        delivery_persons_data.append({
            'id': person.id,
            'username': person.username,
            'full_name': person.get_full_name(),
            'phone_number': getattr(person.delivery_profile, 'phone', person.phone),
            'vehicle_type': getattr(person.delivery_profile, 'vehicle_type', 'Non spécifié'),
            'rating': getattr(person.delivery_profile, 'rating', 0),
            'distance': round(distance, 2) if distance else None,
            'latitude': float(person.delivery_person_profile.location_point.latitude) if hasattr(person, 'delivery_person_profile') and person.delivery_person_profile.location_point else 9.6412,
            'longitude': float(person.delivery_person_profile.location_point.longitude) if hasattr(person, 'delivery_person_profile') and person.delivery_person_profile.location_point else -13.5784,
            'existing_request': existing_request,
        })
    
    context = {
        'delivery': delivery,
        'delivery_persons': delivery_persons_data,
        'delivery_location': delivery.location_point,
    }
    
    return render(request, 'deliveries/delivery_map.html', context)

@login_required
def request_delivery(request, delivery_id):
    """Faire une demande de livraison (livreur)"""
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
        # Calculer un coût proposé
        proposed_cost = delivery.calculate_delivery_cost()
        form = DeliveryRequestForm(initial={'proposed_cost': proposed_cost})
    
    return render(request, 'deliveries/request_form.html', {
        'form': form,
        'delivery': delivery
    })

@login_required
@require_POST
def accept_delivery_request(request, request_id):
    """Accepter une demande de livraison (vendeur)"""
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
        message=f'Votre demande pour la livraison {delivery.tracking_number} a été acceptée.',
        notification_type='delivery_accepted',
        url=reverse('deliveries:detail', kwargs={'pk': delivery.id})
    )
    
    return JsonResponse({'success': True})

@login_required
def assign_delivery_person(request, delivery_id):
    """Assigner directement un livreur avec proposition de prix (vendeur)"""
    if request.method == 'POST':
        delivery = get_object_or_404(Delivery, id=delivery_id)
        
        # Vérifier que c'est le vendeur
        if not delivery.order.items.filter(product__seller=request.user).exists():
            return JsonResponse({'success': False, 'error': 'Non autorisé'})
        
        delivery_person_id = request.POST.get('delivery_person_id')
        proposed_cost = request.POST.get('proposed_cost')
        paid_by = request.POST.get('paid_by', 'buyer')
        
        delivery_person = get_object_or_404(User, id=delivery_person_id, user_type='delivery')
        
        # Créer ou mettre à jour la demande
        delivery_request, created = DeliveryRequest.objects.get_or_create(
            delivery=delivery,
            delivery_person=delivery_person,
            defaults={
                'proposed_cost': proposed_cost,
                'message': f'Proposition directe du vendeur: {proposed_cost} GNF'
            }
        )
        
        if not created:
            delivery_request.proposed_cost = proposed_cost
            delivery_request.save()
        
        # Mettre à jour qui paie
        delivery.paid_by = paid_by
        delivery.save()
        
        # Notifier le livreur
        Notification.objects.create(
            user=delivery_person,
            title='Proposition de livraison',
            message=f'Le vendeur vous propose une livraison pour {proposed_cost} GNF.',
            notification_type='delivery_request',
            url=reverse('deliveries:detail', kwargs={'pk': delivery.id})
        )
        
        messages.success(request, f'Proposition envoyée à {delivery_person.username}')
        return redirect('deliveries:delivery_map', delivery_id=delivery_id)
    
    return redirect('deliveries:list')

@login_required
def start_delivery(request, delivery_id):
    """Démarrer une livraison (livreur)"""
    delivery = get_object_or_404(Delivery, id=delivery_id, delivery_person=request.user)
    
    if delivery.status == 'assigned':
        delivery.status = 'in_progress'
        delivery.save()
        
        # Notifier l'acheteur
        Notification.objects.create(
            user=delivery.order.user,
            title='Livraison en cours',
            message=f'Votre livraison {delivery.tracking_number} a été prise en charge.',
            notification_type='order_shipped',
            url=reverse('orders:detail', kwargs={'pk': delivery.order.id})
        )
        
        messages.success(request, 'Livraison démarrée.')
    else:
        messages.error(request, 'Cette livraison ne peut pas être démarrée.')
    
    return redirect('deliveries:detail', pk=delivery_id)

@login_required
def complete_delivery(request, delivery_id):
    """Terminer une livraison (livreur)"""
    delivery = get_object_or_404(Delivery, id=delivery_id, delivery_person=request.user)
    
    if delivery.status == 'in_progress':
        delivery.status = 'completed'
        delivery.actual_delivery_time = timezone.now()
        delivery.save()
        
        # Mettre à jour la commande
        delivery.order.status = 'delivered'
        delivery.order.save()
        
        # Notifier l'acheteur
        Notification.objects.create(
            user=delivery.order.user,
            title='Livraison terminée',
            message=f'Votre commande {delivery.tracking_number} a été livrée avec succès.',
            notification_type='order_delivered',
            url=reverse('orders:detail', kwargs={'pk': delivery.order.id})
        )
        
        messages.success(request, 'Livraison terminée avec succès.')
    else:
        messages.error(request, 'Cette livraison ne peut pas être terminée.')
    
    return redirect('deliveries:detail', pk=delivery_id)

@login_required
def rate_delivery(request, delivery_id):
    """Noter une livraison (acheteur)"""
    delivery = get_object_or_404(Delivery, id=delivery_id, order__user=request.user)
    
    if delivery.status != 'completed':
        messages.error(request, 'Vous ne pouvez noter que les livraisons terminées.')
        return redirect('deliveries:detail', pk=delivery_id)
    
    if hasattr(delivery, 'rating'):
        messages.info(request, 'Vous avez déjà noté cette livraison.')
        return redirect('deliveries:detail', pk=delivery_id)
    
    if request.method == 'POST':
        form = DeliveryRatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.delivery = delivery
            rating.created_by = request.user
            rating.save()
            
            # Mettre à jour la note moyenne du livreur
            if delivery.delivery_person and hasattr(delivery.delivery_person, 'delivery_profile'):
                ratings = DeliveryRating.objects.filter(delivery__delivery_person=delivery.delivery_person)
                avg_rating = ratings.aggregate(models.Avg('rating'))['rating__avg']
                delivery.delivery_person.delivery_profile.rating = avg_rating or 0
                delivery.delivery_person.delivery_profile.save()
            
            messages.success(request, 'Votre évaluation a été enregistrée.')
            return redirect('deliveries:detail', pk=delivery_id)
    else:
        form = DeliveryRatingForm()
    
    return render(request, 'deliveries/rate_form.html', {
        'form': form,
        'delivery': delivery
    })
@login_required
def toggle_availability(request):
    """Basculer la disponibilité du livreur"""
    if not request.user.is_delivery:
        return JsonResponse({'success': False, 'error': 'Non autorisé'})
    
    if request.method == 'POST':
        profile = request.user.delivery_profile
        profile.is_available = not profile.is_available
        profile.save()
        
        return JsonResponse({
            'success': True,
            'is_available': profile.is_available
        })
    
    return JsonResponse({'success': False})

@login_required
def seller_delivery_dashboard(request):
    """Tableau de bord des livraisons pour vendeurs"""
    if request.user.user_type != 'seller':
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:home')
    
    # Livraisons en attente d'assignation
    pending_deliveries = Delivery.objects.filter(
        order__items__product__seller=request.user,
        status='pending',
        delivery_person__isnull=True
    ).distinct()
    
    # Livraisons en cours
    active_deliveries = Delivery.objects.filter(
        order__items__product__seller=request.user,
        status__in=['assigned', 'in_progress']
    ).distinct()
    
    # Livraisons terminées récemment
    completed_deliveries = Delivery.objects.filter(
        order__items__product__seller=request.user,
        status='completed'
    ).distinct()[:5]
    
    context = {
        'pending_deliveries': pending_deliveries,
        'active_deliveries': active_deliveries,
        'completed_deliveries': completed_deliveries,
    }
    
    return render(request, 'deliveries/seller_dashboard.html', context)