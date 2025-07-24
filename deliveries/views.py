from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Avg
from .models import Delivery, DeliveryRequest, DeliveryRating, DeliveryPerson, DeliveryNegotiation
from .forms import DeliveryRequestForm, DeliveryRatingForm
from geolocation.models import UserLocation, LocationPoint
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from notifications.models import Notification
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from geolocation.distance_calculator import DistanceCalculator

User = get_user_model()

class DeliveryListView(LoginRequiredMixin, ListView):
    model = Delivery
    template_name = 'deliveries/list.html'
    context_object_name = 'deliveries'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Delivery.objects.select_related('order', 'delivery_person', 'location_point', 'delivery_zone')
        
        if self.request.user.is_delivery:
            queryset = queryset.filter(
                Q(delivery_person=self.request.user) |
                Q(status='pending')
            )
        elif self.request.user.is_buyer:
            queryset = queryset.filter(order__user=self.request.user)
        elif self.request.user.is_seller:
            queryset = queryset.filter(order__items__product__seller=self.request.user).distinct()
        
        return queryset.order_by('-created_at')

class DeliveryDetailView(LoginRequiredMixin, DetailView):
    model = Delivery
    template_name = 'deliveries/detail.html'
    context_object_name = 'delivery'
    pk_url_kwarg = 'pk'  # Explicitement défini pour utiliser <int:pk>
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        delivery = self.get_object()
        
        context['user_locations'] = UserLocation.objects.filter(user=delivery.order.user)
        
        # Ajouter les informations de distance
        distance_info = delivery.get_distance_info()
        context['distance_info'] = distance_info
        
        if self.request.user.is_delivery:
            context['user_request'] = DeliveryRequest.objects.filter(
                delivery=delivery,
                delivery_person=self.request.user
            ).first()
            context['request_form'] = DeliveryRequestForm(initial={'proposed_cost': delivery.delivery_cost})
        
        if delivery.status == 'completed' and self.request.user == delivery.order.user:
            context['rating_form'] = DeliveryRatingForm()
        
        return context

@login_required
def available_deliveries(request):
    if not request.user.is_delivery:
        messages.error(request, _('Vous devez être livreur pour accéder à cette page.'))
        return redirect('deliveries:list')
    
    deliveries = Delivery.objects.filter(
        status='pending',
        delivery_person__isnull=True
    ).select_related('order', 'location_point', 'delivery_zone')
    
    return render(request, 'deliveries/available.html', {'deliveries': deliveries})

@login_required
def propose_delivery_cost(request, delivery_id):
    delivery = get_object_or_404(Delivery, id=delivery_id, order__items__product__seller=request.user)
    
    if delivery.status != 'pending':
        messages.error(request, _('Vous ne pouvez proposer un prix que pour les livraisons en attente.'))
        return redirect('deliveries:detail', pk=delivery_id)
    
    if request.method == 'POST':
        form = DeliveryRequestForm(request.POST)
        paid_by = request.POST.get('paid_by', 'buyer')
        if form.is_valid() and paid_by in ['buyer', 'seller']:
            delivery.delivery_cost = form.cleaned_data['proposed_cost']
            delivery.paid_by = paid_by
            delivery.save()
            
            delivery_persons = DeliveryPerson.objects.filter(availability_status='available')
            for delivery_person in delivery_persons:
                Notification.objects.create(
                    user=delivery_person.user,
                    title=_('Nouvelle proposition de livraison'),
                    message=f"Proposition pour #{delivery.tracking_number} : {delivery.delivery_cost}€, payé par {delivery.get_paid_by_display}.",
                    notification_type='delivery_request',
                    url=reverse('deliveries:detail', kwargs={'pk': delivery.id})
                )
            
            messages.success(request, _('Votre proposition de prix a été enregistrée et envoyée aux livreurs !'))
            return redirect('deliveries:delivery_requests', delivery_id=delivery.id)
    else:
        form = DeliveryRequestForm(initial={'proposed_cost': delivery.delivery_cost})
    
    return render(request, 'deliveries/propose_delivery.html', {
        'form': form,
        'delivery': delivery,
        'estimated_cost': delivery.delivery_cost
    })

@login_required
def request_delivery(request, delivery_id):
    if not request.user.is_delivery:
        messages.error(request, _('Vous devez être livreur pour faire une demande.'))
        return redirect('deliveries:list')
    
    delivery = get_object_or_404(Delivery, id=delivery_id, status='pending')
    
    if request.method == 'POST':
        form = DeliveryRequestForm(request.POST)
        if form.is_valid():
            delivery_request = form.save(commit=False)
            delivery_request.delivery = delivery
            delivery_request.delivery_person = request.user
            delivery_request.save()
            
            Notification.objects.create(
                user=delivery.order.items.first().product.seller,
                title=_('Nouvelle demande de livraison'),
                message=f"Demande pour #{delivery.tracking_number} par {request.user.username} : {delivery_request.proposed_cost}€, payé par {delivery.get_paid_by_display}.",
                notification_type='delivery_request',
                url=reverse('deliveries:delivery_requests', kwargs={'delivery_id': delivery.id})
            )
            
            messages.success(request, _('Votre demande de livraison a été envoyée !'))
            return redirect('deliveries:detail', pk=delivery.id)
    else:
        form = DeliveryRequestForm(initial={'proposed_cost': delivery.delivery_cost})
    
    return render(request, 'deliveries/request_form.html', {
        'form': form,
        'delivery': delivery
    })

@login_required
def delivery_requests(request, delivery_id):
    delivery = get_object_or_404(Delivery, id=delivery_id, order__items__product__seller=request.user)
    
    if delivery.status != 'pending':
        messages.error(request, _('Vous ne pouvez gérer les demandes que pour les livraisons en attente.'))
        return redirect('deliveries:detail', pk=delivery_id)
    
    requests = DeliveryRequest.objects.filter(delivery=delivery).select_related('delivery_person__delivery_person_profile')
    
    return render(request, 'deliveries/delivery_requests.html', {
        'delivery': delivery,
        'requests': requests,
        'map_url': reverse('geolocation:delivery_person_map', kwargs={'delivery_id': delivery.id})
    })

@login_required
def accept_delivery_request(request, request_id):
    delivery_request = get_object_or_404(DeliveryRequest, id=request_id)
    
    if request.user != delivery_request.delivery.order.items.first().product.seller:
        return JsonResponse({'success': False, 'message': _('Vous n\'avez pas la permission d\'accepter cette demande.')}, status=403)
    
    delivery = delivery_request.delivery
    if delivery.status != 'pending':
        return JsonResponse({'success': False, 'message': _('Vous ne pouvez accepter une demande que pour les livraisons en attente.')}, status=400)
    
    delivery.delivery_person = delivery_request.delivery_person
    delivery.delivery_cost = delivery_request.proposed_cost
    delivery.status = 'assigned'
    delivery.save()
    
    delivery_request.is_accepted = True
    delivery_request.save()
    
    Notification.objects.create(
        user=delivery.order.user,
        title=_('Livreur assigné'),
        message=f"Un livreur a été assigné pour la livraison #{delivery.tracking_number} pour {delivery.delivery_cost}€, payé par {delivery.get_paid_by_display}.",
        notification_type='delivery_assigned',
        url=reverse('deliveries:detail', kwargs={'pk': delivery.id})
    )
    
    Notification.objects.create(
        user=delivery.delivery_person,
        title=_('Livraison assignée'),
        message=f"Vous avez été assigné à la livraison #{delivery.tracking_number}. Veuillez commencer la livraison.",
        notification_type='delivery_assigned',
        url=reverse('deliveries:detail', kwargs={'pk': delivery.id})
    )
    
    DeliveryRequest.objects.filter(delivery=delivery).exclude(id=request_id).delete()
    
    return JsonResponse({'success': True, 'message': _('Demande de livraison acceptée !')})

@login_required
def confirm_delivery_cost(request, delivery_id):
    delivery = get_object_or_404(Delivery, id=delivery_id, order__items__product__seller=request.user)
    
    if delivery.status != 'pending':
        messages.error(request, _('Cette livraison n\'est pas en attente de confirmation.'))
        return redirect('deliveries:detail', pk=delivery_id)
    
    if request.method == 'POST':
        proposed_cost = request.POST.get('delivery_cost')
        paid_by = request.POST.get('paid_by', 'buyer')
        try:
            proposed_cost = float(proposed_cost)
            if paid_by not in ['buyer', 'seller']:
                messages.error(request, _('Valeur invalide pour le payeur.'))
                return redirect('deliveries:detail', pk=delivery_id)
        # Utiliser le nouveau système de calcul de distance
        delivery_location = delivery.location_point
        if not delivery_location:
            messages.error(request, _("Aucune localisation définie pour cette livraison."))
            return redirect('deliveries:detail', pk=delivery_id)
        
        # Obtenir les livreurs à proximité
        nearby_persons = delivery_location.get_nearby_delivery_persons(radius_km=15)
        
        # Formater les données pour le template
        delivery_persons = []
        for person_info in nearby_persons:
            person = person_info['person']
            delivery_persons.append({
                'person': person,
                'distance_km': person_info['distance_km'],
                'duration_min': person_info['duration_min'],
                'requests': person.delivery_requests.filter(delivery=delivery)
            })
    return render(request, 'deliveries/confirm_delivery_cost.html', {
        'delivery': delivery
    })

@login_required
def start_delivery(request, delivery_id):
    delivery = get_object_or_404(Delivery, id=delivery_id, delivery_person=request.user)
        # Calculer les informations de distance pour l'affichage
        distance_info = delivery.get_distance_info()
        delivery_cost = None
        if distance_info and distance_info['success'] and delivery.delivery_zone:
            delivery_cost = delivery.delivery_zone.calculate_delivery_cost(distance_info['distance_km'])
        
    
    if delivery.status == 'assigned':
            'delivery_persons': delivery_persons,
        delivery.save()
            'mapbox_api_key': settings.MAPBOX_API_KEY,
            'distance_info': distance_info,
            'delivery_cost': delivery_cost
    else:
        messages.error(request, _('Cette livraison ne peut pas être démarrée.'))
    
    return redirect('deliveries:detail', pk=delivery_id)

@login_required
def complete_delivery(request, delivery_id):
    delivery = get_object_or_404(Delivery, id=delivery_id, delivery_person=request.user)
    
    if delivery.status == 'in_progress':
        delivery.status = 'completed'
        delivery.actual_delivery_time = timezone.now()
        delivery.save()
        
        delivery.order.status = 'delivered'
        delivery.order.save()
        
        messages.success(request, _('Livraison terminée !'))
    else:
        messages.error(request, _('Cette livraison ne peut pas être terminée.'))
    
    return redirect('deliveries:detail', pk=delivery_id)

@login_required
def rate_delivery(request, delivery_id):
    delivery = get_object_or_404(Delivery, id=delivery_id, order__user=request.user)
    
    if delivery.status != 'completed':
        messages.error(request, _('Vous ne pouvez évaluer que les livraisons terminées.'))
        return redirect('deliveries:detail', pk=delivery_id)
    
    if request.method == 'POST':
        form = DeliveryRatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.delivery = delivery
            rating.created_by = request.user
            rating.save()
            
            delivery_person = delivery.delivery_person
            if delivery_person and delivery_person.delivery_person_profile:
                profile = delivery_person.delivery_person_profile
                ratings = DeliveryRating.objects.filter(delivery__delivery_person=delivery_person)
                avg_rating = ratings.aggregate(Avg('rating'))['rating__avg']
                profile.rating = avg_rating or 0
                profile.save()
            
            messages.success(request, _('Votre évaluation a été enregistrée !'))
            return redirect('deliveries:detail', pk=delivery_id)
    else:
        form = DeliveryRatingForm()
    
    return render(request, 'deliveries/rate_form.html', {
        'form': form,
        'delivery': delivery
    })

@login_required
def select_delivery_location(request, delivery_id):
    delivery = get_object_or_404(Delivery, id=delivery_id)
    
    if request.user != delivery.order.user:
        messages.error(request, _("Vous n'avez pas la permission de modifier cette livraison."))
        return redirect('deliveries:detail', pk=delivery_id)
    
    if request.method == 'POST':
        location_type = request.POST.get('location_type')
        if location_type == 'existing':
            location_id = request.POST.get('location_id')
            if location_id:
                user_location = get_object_or_404(UserLocation, id=location_id, user=request.user)
                delivery.location_point = user_location.location_point
                delivery.save()
                messages.success(request, _("Adresse de livraison mise à jour !"))
                return redirect('deliveries:detail', pk=delivery_id)
        elif location_type == 'manual':
            order = delivery.order
            order.shipping_first_name = request.POST.get('shipping_first_name', order.shipping_first_name)
            order.shipping_last_name = request.POST.get('shipping_last_name', order.shipping_last_name)
            order.shipping_address = request.POST.get('shipping_address', order.shipping_address)
            order.shipping_city = request.POST.get('shipping_city', order.shipping_city)
            order.shipping_postal_code = request.POST.get('shipping_postal_code', order.shipping_postal_code)
            order.shipping_country = request.POST.get('shipping_country', order.shipping_country)
            order.shipping_phone = request.POST.get('shipping_phone', order.shipping_phone)
            order.save()
            delivery.location_point = None
            delivery.save()
            messages.success(request, _("Adresse de livraison manuelle mise à jour !"))
            return redirect('deliveries:detail', pk=delivery_id)
    
    user_locations = UserLocation.objects.filter(user=request.user)
    return render(request, 'deliveries/select_location.html', {
        'delivery': delivery,
        'user_locations': user_locations
    })

@login_required
def share_qr_code(request, delivery_id):
    delivery = get_object_or_404(Delivery, id=delivery_id, order__items__product__seller=request.user)
    
    if not delivery.order.payment or not delivery.order.payment.qr_code_image:
        messages.error(request, _("Aucun QR code disponible pour cette livraison."))
        return redirect('deliveries:detail', pk=delivery_id)
    
    if not delivery.delivery_person:
        messages.error(request, _("Aucun livreur assigné à cette livraison."))
        return redirect('deliveries:detail', pk=delivery_id)
    
    subject = _("QR Code pour la livraison #") + str(delivery.tracking_number)
    message = _(
        f"Bonjour {delivery.delivery_person.username},\n\n"
        f"Le QR code pour la commande #{delivery.order.id|slice:':8'} est disponible. "
        f"Veuillez le présenter à {'l\'acheteur' if delivery.paid_by == 'buyer' else 'le vendeur'} pour confirmer le paiement à la livraison.\n\n"
        f"Code de confirmation : {delivery.order.payment.confirmation_code}\n"
        f"Adresse de livraison : {delivery.location_point.full_address if delivery.location_point else delivery.order.full_shipping_address}\n"
        f"Adresse du vendeur : {delivery.order.items.first().product.seller.full_address}\n"
        f"Prix de livraison : {delivery.delivery_cost}€\n"
        f"Payé par : {delivery.get_paid_by_display}\n"
        f"Lien vers les détails de la livraison : {request.build_absolute_uri(reverse('deliveries:detail', kwargs={'pk': delivery.id}))}\n\n"
        f"Cordialement,\nL'équipe E-Commerce"
    )
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [delivery.delivery_person.email]
    
    try:
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
            html_message=(
                f"<p>Bonjour {delivery.delivery_person.username},</p>"
                f"<p>Le QR code pour la commande #{delivery.order.id|slice:':8'} est disponible. "
                f"Veuillez le présenter à {'l\'acheteur' if delivery.paid_by == 'buyer' else 'le vendeur'} pour confirmer le paiement.</p>"
                f"<p><img src='{request.build_absolute_uri(delivery.order.payment.qr_code_image.url)}' alt='QR Code' style='max-width: 200px;'></p>"
                f"<p><strong>Code de confirmation :</strong> {delivery.order.payment.confirmation_code}</p>"
                f"<p><strong>Adresse de livraison :</strong> {delivery.location_point.full_address if delivery.location_point else delivery.order.full_shipping_address}</p>"
                f"<p><strong>Adresse du vendeur :</strong> {delivery.order.items.first().product.seller.full_address}</p>"
                f"<p><strong>Prix de livraison :</strong> {delivery.delivery_cost}€</p>"
                f"<p><strong>Payé par :</strong> {delivery.get_paid_by_display}</p>"
                f"<p><a href='{request.build_absolute_uri(reverse('deliveries:detail', kwargs={'pk': delivery.id}))}'>Voir les détails de la livraison</a></p>"
                f"<p>Cordialement,<br>L'équipe E-Commerce</p>"
            )
        )
        messages.success(request, _("Le QR code et les informations de livraison ont été transmis au livreur avec succès !"))
    except Exception as e:
        messages.error(request, _("Erreur lors de l'envoi du QR code au livreur : ") + str(e))
    
    return redirect('deliveries:detail', pk=delivery_id)

@login_required
def assign_delivery_person(request, delivery_id):
    """Vue pour permettre au vendeur de sélectionner un livreur et transmettre les informations"""
    delivery = get_object_or_404(Delivery, id=delivery_id, order__items__product__seller=request.user)
    
    if delivery.status != 'pending':
        return JsonResponse({'success': False, 'message': _('Vous ne pouvez assigner un livreur que pour les livraisons en attente.')}, status=400)
    
    if request.method == 'POST':
        delivery_person_id = request.POST.get('delivery_person_id')
        proposed_cost = request.POST.get('proposed_cost')
        paid_by = request.POST.get('paid_by', 'buyer')
        
        if not delivery_person_id or not proposed_cost or paid_by not in ['buyer', 'seller']:
            return JsonResponse({'success': False, 'message': _('Veuillez sélectionner un livreur, indiquer un prix et choisir qui paie.')}, status=400)
        
        try:
            delivery_person = DeliveryPerson.objects.get(user__id=delivery_person_id, availability_status='available')
            proposed_cost = float(proposed_cost)
            
            # Vérifier si une demande existe déjà
            existing_request = DeliveryRequest.objects.filter(delivery=delivery, delivery_person=delivery_person.user).first()
            if existing_request:
                return JsonResponse({'success': False, 'message': _('Une demande existe déjà pour ce livreur.')}, status=400)
            
            # Créer une demande de livraison
            delivery_request = DeliveryRequest.objects.create(
                delivery=delivery,
                delivery_person=delivery_person.user,
                proposed_cost=proposed_cost,
                message=f"Proposition de livraison pour #{delivery.tracking_number} par le vendeur"
            )
            
            # Mettre à jour paid_by
            delivery.paid_by = paid_by
            delivery.save()
            
            # Envoyer une notification au livreur
            Notification.objects.create(
                user=delivery_person.user,
                title=_('Nouvelle proposition de livraison'),
                message=f"Le vendeur vous propose la livraison #{delivery.tracking_number} pour {proposed_cost}€, payé par {delivery.get_paid_by_display}. Veuillez accepter ou refuser.",
                notification_type='delivery_request',
                url=reverse('deliveries:request', kwargs={'delivery_id': delivery.id})
            )
            
            return JsonResponse({'success': True, 'message': _('Proposition envoyée au livreur. En attente de sa confirmation.')})
        
        except DeliveryPerson.DoesNotExist:
            return JsonResponse({'success': False, 'message': _('Livreur non disponible ou invalide.')}, status=400)
        except ValueError:
            return JsonResponse({'success': False, 'message': _('Prix invalide.')}, status=400)
    
@login_required
def delivery_dashboard(request):
    """Tableau de bord pour les livreurs"""
    if not request.user.is_delivery:
        messages.error(request, "Vous devez être livreur pour accéder à cette page.")
        return redirect('core:home')
    
    # Statistiques
    stats = {
        'total_deliveries': request.user.deliveries.count(),
        'completed_deliveries': request.user.deliveries.filter(status='completed').count(),
        'average_rating': request.user.delivery_profile.rating,
        'earnings': 0  # À calculer selon votre logique métier
    }
    
    # Livraisons actives
    active_deliveries = request.user.deliveries.filter(
        status__in=['assigned', 'in_progress']
    ).select_related('order')
    
    # Dernières évaluations
    recent_ratings = DeliveryRating.objects.filter(
        delivery__delivery_person=request.user
    ).order_by('-created_at')[:5]
    
    return render(request, 'deliveries/delivery_dashboard.html', {
        'stats': stats,
        'active_deliveries': active_deliveries,
        'recent_ratings': recent_ratings
    })
    return JsonResponse({'success': False, 'message': _('Méthode non autorisée.')}, status=405)
@login_required
def toggle_availability(request):
    """Basculer la disponibilité du livreur"""
    if not request.user.is_delivery:
        return redirect('core:home')
    
    if request.method == 'POST':
        profile = request.user.delivery_profile
        profile.is_available = not profile.is_available
        profile.save()
        
        status = "disponible" if profile.is_available else "indisponible"
        messages.success(request, f"Vous êtes maintenant {status} pour les livraisons.")
    
    return redirect('deliveries:delivery_dashboard')

@login_required
def negotiate_delivery(request, delivery_id):
    delivery = get_object_or_404(Delivery, id=delivery_id, order__items__product__seller=request.user)
    if request.method == 'POST':
        proposed_price = request.POST.get('proposed_price')
        delivery_person_id = request.POST.get('delivery_person')
        try:
            proposed_price = float(proposed_price)
            delivery_person = User.objects.get(id=delivery_person_id, user_type='delivery')
            negotiation = DeliveryNegotiation.objects.create(
                delivery=delivery,
                seller=request.user,
                delivery_person=delivery_person,
                proposed_price=proposed_price
            )
            Notification.objects.create(
                user=delivery_person,
                title="Nouvelle proposition de livraison",
                message=f"Le vendeur {request.user.username} propose {proposed_price} pour la livraison #{delivery.tracking_number}.",
                notification_type='delivery_request',
                url=reverse('deliveries:detail', kwargs={'pk': delivery.id})
            )
            return JsonResponse({'success': True, 'message': 'Proposition envoyée.'})
        except (ValueError, User.DoesNotExist):
            return JsonResponse({'success': False, 'message': 'Erreur dans la proposition.'}, status=400)
    delivery_persons = User.objects.filter(user_type='delivery')
    return render(request, 'deliveries/negotiate.html', {
        'delivery': delivery,
        'delivery_persons': delivery_persons
    })